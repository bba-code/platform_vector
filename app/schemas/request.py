from pydantic import BaseModel
from typing import Optional

class SetFileRequest(BaseModel):
    platform_company_id: int
    platform_file_id: int
    file_text: str

class DeleteFileRequest(BaseModel):
    platform_company_id: int
    platform_file_id: int

class MessageRequestParams(BaseModel):
    # Эти параметры будут передаваться как query parameters, не в теле запроса
    # Поэтому отдельная схема для тела запроса GET не нужна
    # Определим их прямо в эндпоинте
    pass 

# Схема запроса для обработки файла (чанкинг + эмбеддинг)
class ProcessFileRequest(BaseModel):
    text: str 

# Схема запроса для поиска по чанкам и генерации ответа
class MessagePGRequest(BaseModel):
    query_text: str 