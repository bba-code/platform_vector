from pydantic import BaseModel
from typing import Optional

from app.schemas.message import Message

class SetFileResponse(BaseModel):
    message: str
    platform_company_id: int
    platform_file_id: int

class DeleteFileResponse(BaseModel):
    message: str
    platform_company_id: int
    platform_file_id: int

class MessageResponse(BaseModel):
    ai_response: str
    user_message: Message # Сохраненное сообщение пользователя
    ai_message: Message   # Сохраненное сообщение AI

class ErrorResponse(BaseModel):
    detail: str

# Схема ответа для эндпоинта промпта
class PromptResponse(BaseModel):
    ai_response: Optional[str] = None # Текст ответа от AI или None при ошибке 