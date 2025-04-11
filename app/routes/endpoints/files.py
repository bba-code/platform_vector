import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status, Path # Added Path
from sqlalchemy.orm import Session
import tempfile
import os # Для удаления временного файла

from app.core.database import get_db
from app import crud, schemas
from app.utils import openai_client

logger = logging.getLogger(__name__)

router = APIRouter()

# Define a basic response schema if not already present in schemas.response
# namespace schemas.response:
# class DeleteFileResponse(BaseModel):
#     platform_company_id: int
#     platform_file_id: str
#     message: str

@router.post("/", response_model=schemas.response.SetFileResponse)
def set_openai_file(
    *, 
    db: Session = Depends(get_db),
    # Добавляем Depends() обратно, чтобы FastAPI искал параметры в query/form
    request: schemas.request.SetFileRequest = Depends()
) -> schemas.response.SetFileResponse:

    # 1. Проверяем существование компании
    company = crud.company.get_by_platform_id(db, platform_company_id=request.platform_company_id)
    if not company:
        logger.warning(f"Компания с ID {request.platform_company_id} не найдена. Создание новой компании и векторного хранилища.")
        try:
            # Создаем векторное хранилище в OpenAI
            vector_store_name = f"Company_{request.platform_company_id}_Store"
            vector_store = openai_client.create_vector_store(name=vector_store_name)
            vector_store_id = vector_store.id
            logger.info(f"Создано векторное хранилище OpenAI с ID: {vector_store_id} для компании {request.platform_company_id}")

            company_in = schemas.company.CompanyCreate(
                platform_company_id=request.platform_company_id,
                openai_vector_store_id=vector_store_id
            )
            company = crud.company.create(db=db, obj_in=company_in)
            logger.info(f"Создана запись для компании ID {company.id} (platform_id: {company.platform_company_id}) в базе данных.")

        except Exception as e:
            logger.error(f"Ошибка при создании компании {request.platform_company_id} или векторного хранилища: {e}")
            # Если векторное хранилище было создано, но запись в БД не удалась, удаляем хранилище
            if 'vector_store_id' in locals() and vector_store_id:
                try:
                    logger.warning(f"Попытка удалить векторное хранилище {vector_store_id} из-за ошибки сохранения компании в БД.")
                    openai_client.delete_vector_store(vector_store_id)
                except Exception as delete_exc:
                    logger.error(f"Не удалось удалить векторное хранилище {vector_store_id} после ошибки: {delete_exc}")
                    # Можно добавить дополнительную логику обработки этой ошибки

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при инициализации новой компании"
            )
    else:
        logger.info(f"Компания {company.platform_company_id} (ID: {company.id}) найдена. Vector Store ID: {company.openai_vector_store_id}")

    # --- Блок обработки файла (создание/обновление) ---
    openai_file_id = None
    db_file = None
    tmp_file_path = None
    vector_store_id = company.openai_vector_store_id # Получаем ID хранилища

    if not vector_store_id:
            logger.error(f"У компании {company.platform_company_id} (ID: {company.id}) отсутствует ID векторного хранилища. Невозможно обработать файл.")
            raise HTTPException(status_code=500, detail="Ошибка конфигурации компании: отсутствует vector_store_id")

    try:
        # Используем метод get_by_platform_ids для поиска файла
        db_file = crud.file.get_by_platform_ids(db, platform_company_id=request.platform_company_id, platform_file_id=request.platform_file_id)

        if db_file:
            # --- Логика ОБНОВЛЕНИЯ файла ---
            logger.info(f"Файл с platform_id {request.platform_file_id} уже существует в базе данных (ID: {db_file.id}, OpenAI ID: {db_file.openai_file_id}). Обновление файла.")
            old_openai_file_id = db_file.openai_file_id
            new_openai_file_id = None # Инициализация для блока except
            tmp_file_path = None # Инициализация для finally

            try:
                # Формируем префикс для имени файла используя platform IDs
                filename_prefix = f"Company_{request.platform_company_id}-File_{request.platform_file_id}-"

                # Создаем временный файл для нового содержимого с новым префиксом
                with tempfile.NamedTemporaryFile(mode='w', delete=False, prefix=filename_prefix, suffix=".txt", encoding='utf-8') as tmp_file:
                    tmp_file.write(request.file_text)
                    tmp_file_path = tmp_file.name
                logger.info(f"Временный файл для обновления создан: {tmp_file_path}")

                # --- Операции с OpenAI и БД внутри try ---
                # 1. Удаляем старую СВЯЗЬ файла из Vector Store
                if old_openai_file_id:
                    try:
                        openai_client.delete_file_from_vector_store(vector_store_id=vector_store_id, file_id=old_openai_file_id)
                        logger.info(f"Старая связь файла {old_openai_file_id} удалена из векторного хранилища {vector_store_id}")
                    except Exception as e:
                        logger.warning(f"Не удалось удалить связь старого файла {old_openai_file_id} из хранилища {vector_store_id}: {e}. Возможно, ее там не было.")
                
                # 2. Удаляем старый файл из OpenAI
                if old_openai_file_id:
                     try:
                        openai_client.delete_file(file_id=old_openai_file_id)
                        logger.info(f"Старый файл {old_openai_file_id} удален из OpenAI")
                     except Exception as e:
                         logger.warning(f"Не удалось удалить старый файл {old_openai_file_id} из OpenAI: {e}. Возможно, он уже был удален.")

                # 3. Загружаем новый файл в OpenAI
                new_openai_file_id = openai_client.upload_file(file_path=tmp_file_path, purpose="assistants")
                logger.info(f"Новый файл загружен в OpenAI с ID: {new_openai_file_id}")

                # 4. Добавляем новый файл в Vector Store
                openai_client.add_file_to_vector_store(vector_store_id=vector_store_id, file_id=new_openai_file_id)
                logger.info(f"Новый файл {new_openai_file_id} добавлен в векторное хранилище {vector_store_id}")

                # 5. Обновляем запись в нашей базе данных
                file_update = schemas.file.FileUpdate(openai_file_id=new_openai_file_id)
                db_file = crud.file.update(db=db, db_obj=db_file, obj_in=file_update)
                logger.info(f"Запись файла ID {db_file.id} обновлена в базе данных. Новый OpenAI ID: {db_file.openai_file_id}")

            except Exception as e: # Этот except соответствует try на строке 85
                logger.error(f"Ошибка при обновлении файла platform_id {request.platform_file_id}: {e}")
                if new_openai_file_id:
                    try:
                        logger.warning(f"Попытка удалить новый файл {new_openai_file_id} из OpenAI из-за ошибки обновления.")
                        openai_client.delete_file(new_openai_file_id)
                    except Exception as delete_exc:
                        logger.error(f"Не удалось удалить новый файл {new_openai_file_id} из OpenAI после ошибки: {delete_exc}")
                raise HTTPException(status_code=500, detail="Ошибка при обновлении файла")
            finally: # Этот finally соответствует try на строке 85
                 # Удаляем временный файл
                if tmp_file_path and os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)
                    logger.info(f"Временный файл обновления удален: {tmp_file_path}")

        else:
            # --- Логика СОЗДАНИЯ нового файла ---
            logger.info(f"Файл с platform_id {request.platform_file_id} не найден в базе данных. Создание нового файла.")
            
            vector_store_id = company.openai_vector_store_id
            if not vector_store_id:
                logger.error(f"У компании {company.id} отсутствует ID векторного хранилища для создания файла.")
                raise HTTPException(status_code=500, detail="Ошибка конфигурации компании: отсутствует vector_store_id")

            # Формируем префикс для имени файла используя platform IDs
            filename_prefix = f"Company_{request.platform_company_id}-File_{request.platform_file_id}-"
            tmp_file_path = None # Инициализация
            openai_file_id = None # Инициализация
            
            try:
                # Создаем временный файл с новым префиксом
                with tempfile.NamedTemporaryFile(mode='w', delete=False, prefix=filename_prefix, suffix=".txt", encoding='utf-8') as tmp_file:
                    tmp_file.write(request.file_text)
                    tmp_file_path = tmp_file.name
                logger.info(f"Временный файл создан: {tmp_file_path}")
                
                # Загружаем файл в OpenAI
                openai_file_id = openai_client.upload_file(file_path=tmp_file_path, purpose="assistants")
                logger.info(f"Файл загружен в OpenAI с ID: {openai_file_id}")

                # Добавляем файл в векторное хранилище компании
                openai_client.add_file_to_vector_store(vector_store_id=vector_store_id, file_id=openai_file_id)
                logger.info(f"Файл {openai_file_id} добавлен в векторное хранилище {vector_store_id}")

                # Создаем запись о файле в нашей базе данных
                file_in = schemas.file.FileCreate(
                    platform_file_id=request.platform_file_id,
                    platform_company_id=request.platform_company_id,
                    file_text=request.file_text,
                    openai_file_id=openai_file_id
                )
                db_file = crud.file.create(db=db, obj_in=file_in)
                logger.info(f"Создана запись для файла ID {db_file.id} (platform_id: {db_file.platform_file_id}) в базе данных.")

            except Exception as e:
                logger.error(f"Ошибка при обработке нового файла для platform_id {request.platform_file_id}: {e}")
                if openai_file_id:
                    try:
                        logger.warning(f"Попытка удалить файл {openai_file_id} из OpenAI из-за ошибки.")
                        openai_client.delete_file(openai_file_id)
                    except Exception as delete_exc:
                        logger.error(f"Не удалось удалить файл {openai_file_id} из OpenAI после ошибки: {delete_exc}")
                raise HTTPException(status_code=500, detail="Ошибка при загрузке и регистрации файла")
            finally:
                # Удаляем временный файл
                if tmp_file_path and os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)
                    logger.info(f"Временный файл удален: {tmp_file_path}")

    except Exception as e:
        # Эта секция ловит ошибки ДО начала обработки файла (например, ошибка поиска компании если она не создается)
        # или если ошибка произошла вне блоков try/except внутри if/else
        logger.exception(f"Критическая ошибка при обработке запроса для файла platform_id {request.platform_file_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера при обработке файла: {e}"
        )

    # Финальный ответ POST
    return schemas.response.SetFileResponse(
        platform_company_id=request.platform_company_id,
        platform_file_id=request.platform_file_id,
        message="Файл успешно обработан"
    )


# --- НОВЫЙ ЭНДПОИНТ УДАЛЕНИЯ ---
@router.delete("/{platform_company_id}/{platform_file_id}", response_model=schemas.response.DeleteFileResponse, status_code=status.HTTP_200_OK)
def delete_file(
    *,
    db: Session = Depends(get_db),
    request: schemas.request.DeleteFileRequest = Depends(),
) -> schemas.response.DeleteFileResponse:
    """
    Удаляет файл из OpenAI, открепляет его от векторного хранилища
    и удаляет запись о файле из локальной базы данных.
    """
    logger.info(f"Запрос на удаление файла platform_file_id={request.platform_file_id} для компании platform_company_id={request.platform_company_id}")

    # 1. Найти компанию, чтобы получить vector_store_id
    company = crud.company.get_by_platform_id(db, platform_company_id=request.platform_company_id)
    if not company:
        logger.warning(f"Компания с platform_company_id={request.platform_company_id} не найдена. Невозможно удалить файл.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Компания с ID {request.platform_company_id} не найдена"
        )

    vector_store_id = company.openai_vector_store_id
    if not vector_store_id:
        # Компания есть, но нет хранилища? Странно, но можно продолжить удаление из БД
        logger.warning(f"У компании {request.platform_company_id} (ID: {company.id}) отсутствует openai_vector_store_id. Пропускаем удаление из хранилища.")
        # Не прерываем выполнение, т.к. файл мог быть в БД без ID хранилища

    # 2. Найти файл в локальной базе данных
    db_file = crud.file.get_by_platform_ids(db, platform_company_id=request.platform_company_id, platform_file_id=request.platform_file_id)
    if not db_file:
        logger.warning(f"Файл platform_file_id={request.platform_file_id} для компании {request.platform_company_id} не найден в базе данных.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Файл с ID {request.platform_file_id} для компании {request.platform_company_id} не найден"
        )

    openai_file_id = db_file.openai_file_id
    db_file_id = db_file.id # Сохраняем ID для удаления из БД

    # 3. Открепить файл от Vector Store (если есть ID хранилища и ID файла)
    if vector_store_id and openai_file_id:
        try:
            logger.info(f"Попытка удалить связь файла {openai_file_id} из хранилища {vector_store_id}")
            openai_client.delete_file_from_vector_store(vector_store_id=vector_store_id, file_id=openai_file_id)
            logger.info(f"Связь файла {openai_file_id} успешно удалена из хранилища {vector_store_id}")
        except Exception as e:
            # Логируем ошибку, но продолжаем, чтобы удалить файл из OpenAI и БД
            logger.warning(f"Не удалось удалить связь файла {openai_file_id} из хранилища {vector_store_id}: {e}. Возможно, её уже не было.")
    elif not openai_file_id:
         logger.warning(f"У файла {request.platform_file_id} (DB ID: {db_file_id}) отсутствует OpenAI File ID. Пропускаем удаление из хранилища и OpenAI.")
    elif not vector_store_id:
         logger.warning(f"У компании {request.platform_company_id} отсутствует Vector Store ID. Пропускаем удаление из хранилища для файла {openai_file_id}.")


    # 4. Удалить файл из OpenAI (если есть ID файла)
    if openai_file_id:
        try:
            logger.info(f"Попытка удалить файл {openai_file_id} из OpenAI")
            openai_client.delete_file(file_id=openai_file_id)
            logger.info(f"Файл {openai_file_id} успешно удален из OpenAI")
        except Exception as e:
            # Логируем ошибку, но продолжаем, чтобы удалить запись из БД
            logger.warning(f"Не удалось удалить файл {openai_file_id} из OpenAI: {e}. Возможно, он уже был удален.")

    # 5. Удалить запись о файле из локальной базы данных
    try:
        logger.info(f"Попытка удалить запись о файле из БД (ID: {db_file_id}, platform_file_id: {request.platform_file_id})")
        success = crud.file.remove(db=db, id=db_file_id) # crud.remove должен возвращать удаленный объект или ID/True
        if success: # Проверяем успешность удаления из БД
             logger.info(f"Запись о файле ID {db_file_id} (platform_file_id: {request.platform_file_id}) успешно удалена из БД.")
        else:
             # Это не должно произойти, если crud.remove вызывает исключение при ошибке
             logger.error(f"crud.file.remove вернул неуспешный статус для файла ID {db_file_id}")
             raise HTTPException(status_code=500, detail="Ошибка при удалении файла из базы данных")

    except Exception as e:
        logger.error(f"Критическая ошибка при удалении файла ID {db_file_id} (platform_file_id: {request.platform_file_id}) из базы данных: {e}")
        # На этом этапе файл мог быть удален из OpenAI, но остался в БД. Это плохо.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении записи файла из базы данных"
        )

    # Финальный ответ DELETE
    return schemas.response.DeleteFileResponse(
        platform_company_id=request.platform_company_id,
        platform_file_id=request.platform_file_id,
        message="Файл успешно удален"
    )