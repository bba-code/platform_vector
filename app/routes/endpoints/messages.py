import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app import crud, schemas
from app.utils import openai_client

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get(
    "/",
    response_model=schemas.response.PromptResponse,
    summary="Получение ответа AI по промпту с использованием поиска по файлам компании",
    description="Принимает ID компании и текст запроса (prompt). Находит векторное хранилище компании, \
                 отправляет запрос в OpenAI с использованием поиска по этому хранилищу и возвращает текстовый ответ."
)
def get_ai_prompt_response(
    *, # Делает все параметры query parameters именованными
    db: Session = Depends(get_db),
    platform_company_id: int = Query(..., description="ID компании на платформе"),
    prompt: str = Query(..., description="Текст запроса к AI")
) -> schemas.response.PromptResponse:
    
    logger.info(f"Получен запрос на промпт для компании {platform_company_id}.")

    # 1. Найти компанию и ее vector_store_id
    company = crud.company.get_by_platform_id(db, platform_company_id=platform_company_id)
    if not company:
        logger.error(f"Компания с ID {platform_company_id} не найдена.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Компания с ID {platform_company_id} не найдена"
        )
    
    vector_store_id = company.openai_vector_store_id
    if not vector_store_id:
        logger.error(f"У компании {platform_company_id} (ID: {company.id}) отсутствует ID векторного хранилища OpenAI.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка конфигурации: у компании отсутствует ID векторного хранилища"
        )
    
    logger.info(f"Найден vector_store_id: {vector_store_id} для компании {platform_company_id}.")

    # 2. Вызвать функцию OpenAI для получения ответа
    try:
        ai_text_response = openai_client.get_prompt_response(
            prompt=prompt, 
            vector_store_id=vector_store_id
        )
        
        if ai_text_response is None:
             logger.warning(f"OpenAI клиент вернул None для промпта компании {platform_company_id}. Возможно, текст не был извлечен.")
             # Возвращаем 200 ОК, но с ai_response = None, согласно схеме
             return schemas.response.PromptResponse(ai_response=None)

        logger.info(f"Получен ответ от OpenAI для компании {platform_company_id}.")
        return schemas.response.PromptResponse(ai_response=ai_text_response)

    except ValueError as ve:
        # Ошибка, если метод client.responses.create не найден
        logger.error(f"Ошибка конфигурации OpenAI клиента: {ve}")
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Ошибка конфигурации OpenAI: {ve}"
        )
    except Exception as e:
        logger.error(f"Ошибка при обращении к OpenAI для компании {platform_company_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера при обращении к AI: {e}"
        ) 