from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Базовая схема для File
class FileBase(BaseModel):
    platform_company_id: int
    platform_file_id: int
    file_text: str

# Схема для создания File
class FileCreate(FileBase):
    openai_file_id: Optional[str] = None

# Схема для обновления File
class FileUpdate(BaseModel):
    file_text: Optional[str] = None
    openai_file_id: Optional[str] = None

# Схема для чтения данных File из БД
class FileInDBBase(FileBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    openai_file_id: Optional[str] = None

    class Config:
        # orm_mode = True # Устарело в Pydantic V2
        from_attributes = True # Для Pydantic V2

# Финальная схема для ответа API
class File(FileInDBBase):
    pass 