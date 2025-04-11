import logging
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app import schemas, crud
from app.utils import openai_client

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/query/", 
    response_model=schemas.response.MessagePGResponse,
    summary="Запрос к AI с поиском по ВСЕМ чанкам (pgvector)",
    description="""Принимает текст запроса. Генерирует эмбеддинг запроса, 
                 находит похожие чанки ВО ВСЕЙ базе данных (PostgreSQL + pgvector), 
                 формирует контекст из найденных чанков и отправляет запрос в OpenAI 
                 (используя get_prompt_response2) для получения финального ответа."""
)
def query_with_pgvector(
    request: schemas.request.MessagePGRequest, 
    db: Session = Depends(get_db)
) -> schemas.response.MessagePGResponse:
    
    logger.info(f"Запрос на поиск по ВСЕМ чанкам для запроса: '{request.query_text[:50]}...'")

    # --- Шаг 1: Поиск компании УДАЛЕН ---

    # 2. Получить эмбеддинг для запроса
    try:
        query_embedding = openai_client.get_embedding(text=request.query_text)
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Не удалось сгенерировать эмбеддинг для запроса.")
        logger.info(f"Сгенерирован эмбеддинг для запроса: '{request.query_text[:50]}...'")
    except Exception as e:
        logger.exception(f"Ошибка генерации эмбеддинга: {e}") 
        raise HTTPException(status_code=500, detail=f"Ошибка генерации эмбеддинга запроса: {e}")

    # --- Шаг 3: Поиск ID файлов УДАЛЕН --- 

    # 4. Найти похожие чанки по ВСЕЙ базе (без фильтра file_ids)
    try:
        similar_chunks = crud.chunk.get_similar_chunks(
            db=db,
            query_embedding=query_embedding,
            # file_ids=... # Фильтр по файлам убран
            limit=5 
        )
        logger.info(f"Найдено {len(similar_chunks)} похожих чанков по всей базе.")
    except Exception as e:
        # Уточняем сообщение об ошибке
        logger.exception(f"Ошибка векторного поиска чанков по всей базе: {e}")
        raise HTTPException(status_code=500, detail="Ошибка векторного поиска чанков.")

    # 5. Сформировать контекст и промпт
    if not similar_chunks:
        logger.warning("Похожие чанки не найдены во всей базе.")
        context = "Подходящий контекст не найден."
    else:
        context = "\n\n".join([chunk.text for chunk in similar_chunks if hasattr(chunk, 'text') and chunk.text])
        if not context:
             logger.warning("Найденные чанки не содержат текстовых данных.")
             context = "Подходящий контекст не найден (чанки без текста)."

    # Промпт для новой функции get_prompt_response2
    final_prompt = f"Используя следующий контекст:\n--- КОНТЕКСТ ---\n{context}\n--- КОНЕЦ КОНТЕКСТА ---\n\nОтветь на вопрос: {request.query_text}. Если контекста нет ответь что то по типу что данных по этому вопросу нет."

    # 6. Вызвать OpenAI с использованием get_prompt_response2
    try:
        ai_text_response = openai_client.get_prompt_response2(
            prompt=final_prompt
        )
        
        if ai_text_response is None:
             logger.warning("OpenAI клиент (get_prompt_response2) вернул None.")
             return schemas.response.MessagePGResponse(
                 ai_response="Не удалось сгенерировать ответ AI.", 
                 retrieved_chunks_count=len(similar_chunks)
             )

        logger.info("Сгенерирован финальный ответ AI с помощью get_prompt_response2.")
        return schemas.response.MessagePGResponse(
            ai_response=ai_text_response, 
            retrieved_chunks_count=len(similar_chunks)
        )
    
    except Exception as e:
        logger.exception(f"Ошибка при вызове get_prompt_response2: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации ответа AI: {e}")
 