from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Базовая схема для Company (общие поля)
class CompanyBase(BaseModel):
    platform_company_id: int

# Схема для создания Company (включает токен при создании)
class CompanyCreate(CompanyBase):
    openai_vector_store_id: str
    
# Схема для обновления Company
class CompanyUpdate(BaseModel):
    openai_vector_store_id: Optional[str] = None
    # Добавьте сюда другие поля, которые можно обновлять

# Схема для чтения данных Company из БД (включает id и created_at)
class Company(CompanyBase):
    id: int
    created_at: datetime
    token: str
    openai_vector_store_id: Optional[str] = None

    class Config:
        from_attributes = True 