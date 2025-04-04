from pydantic import BaseModel, validator
from datetime import datetime
from typing import Literal

# Базовая схема для Message
class MessageBase(BaseModel):
    text: str
    user_type: Literal["user", "ai"]
    platform_user_id: int
    platform_company_id: int

# Схема для создания Message
class MessageCreate(MessageBase):
    pass

# Схема для обновления Message (если понадобится)
class MessageUpdate(BaseModel):
    text: str | None = None

# Схема для чтения данных Message из БД
class MessageInDBBase(MessageBase):
    id: int
    created_at: datetime

    class Config:
        # orm_mode = True # Устарело в Pydantic V2
        from_attributes = True # Для Pydantic V2

# Финальная схема для ответа API
class Message(MessageInDBBase):
    pass 