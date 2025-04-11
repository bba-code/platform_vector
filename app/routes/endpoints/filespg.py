import logging
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app import schemas, crud
from app.utils import openai_client

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Вспомогательная функция для чанкинга --- 
def simple_chunker(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """Простой чанкер текста.
    Делит текст на части примерно chunk_size символов с перекрытием chunk_overlap.
    Создает один чанк, если текст короче chunk_size.
    """
    if len(text) <= chunk_size:
        # Если текст короткий, возвращаем его как один чанк
        stripped_text = text.strip()
        return [stripped_text] if stripped_text else [] 

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        next_start = start + chunk_size - chunk_overlap
        if next_start <= start: # Предотвращение бесконечного цикла при большом перекрытии
            next_start = start + chunk_size # Двигаемся дальше без перекрытия в этом случае
        start = next_start
        if start >= len(text):
            break
    return [chunk for chunk in chunks if chunk.strip()]

@router.post(
    "/process/", 
    response_model=schemas.response.ProcessFileResponse,
    summary="Обработка текста файла: сохранение, чанкинг, эмбеддинг",
    description="Принимает текст, сохраняет его в таблицу files2, разбивает на чанки, \
                 получает эмбеддинги для чанков и сохраняет их в таблицу chunks."
)
def process_file_text(
    # Возвращаем Depends() для схемы, чтобы FastAPI искал параметры в query/form
    request: schemas.request.ProcessFileRequest = Depends(),
    db: Session = Depends(get_db)
) -> schemas.response.ProcessFileResponse:
    
    logger.info(f"Запрос на обработку текста файла (длина: {len(request.text)}).")

    # 1. Сохранить оригинальный текст в files2
    try:
        file_in = schemas.files2.Files2Create(text=request.text)
        db_file = crud.files2.create(db=db, obj_in=file_in)
        logger.info(f"Текст сохранен в files2 с ID: {db_file.id}")
    except Exception as e:
        logger.exception(f"Ошибка сохранения текста в files2: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сохранения оригинального текста файла.")

    # 2. Разбить текст на чанки
    chunks_text = simple_chunker(request.text)
    if not chunks_text:
         logger.warning("Текст не был разбит на чанки (возможно, пустой?).")
         return schemas.response.ProcessFileResponse(
             file_id=db_file.id,
             chunks_count=0,
             message="Файл сохранен, но чанки не созданы (текст пустой)."
         )
    logger.info(f"Текст разбит на {len(chunks_text)} чанков.")

    # 3. Получить эмбеддинги и подготовить чанки
    chunks_to_create: List[schemas.chunk.ChunkCreate] = []
    failed_embeddings = 0
    for i, chunk_text in enumerate(chunks_text):
        embedding = None 
        try:
            embedding = openai_client.get_embedding(text=chunk_text)
            if not embedding:
                logger.warning(f"Не удалось получить эмбеддинг для чанка {i} файла {db_file.id}. Чанк будет сохранен без эмбеддинга.")
                failed_embeddings += 1
        except Exception as e:
            logger.exception(f"Ошибка получения эмбеддинга для чанка {i} файла {db_file.id}: {e}. Чанк будет сохранен без эмбеддинга.")
            failed_embeddings += 1
        
        chunk_obj = schemas.chunk.ChunkCreate(
            text=chunk_text,
            index=i,
            file_id=db_file.id,
            embedding=embedding 
        )
        chunks_to_create.append(chunk_obj)
            
    # 4. Сохранить чанки в базу данных (bulk create)
    try:
        if chunks_to_create:
            created_chunks = crud.chunk.create_multi(db=db, objs_in=chunks_to_create)
            logger.info(f"Успешно сохранено {len(created_chunks)} чанков для файла {db_file.id} в БД.")
            if failed_embeddings > 0:
                 message = f"Файл и {len(created_chunks)} чанков успешно обработаны, но для {failed_embeddings} чанков не удалось получить эмбеддинг."
            else:
                 message = f"Файл и {len(created_chunks)} чанков успешно обработаны."
            return schemas.response.ProcessFileResponse(
                file_id=db_file.id,
                chunks_count=len(created_chunks),
                message=message
            )
        else:
            logger.error("Нет чанков для сохранения, хотя текст был разбит.")
            raise HTTPException(status_code=500, detail="Ошибка сохранения чанков: список чанков пуст.")

    except Exception as e:
        logger.exception(f"Ошибка bulk сохранения чанков для файла {db_file.id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сохранения обработанных чанков файла.") 