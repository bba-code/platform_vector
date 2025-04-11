from pydantic import BaseModel
from typing import List, Optional

class ChunkBase(BaseModel):
    text: str
    index: int # int для Pydantic
    file_id: int # int для Pydantic

class ChunkCreate(ChunkBase):
    embedding: Optional[List[float]] = None

class ChunkUpdate(BaseModel):
    # Обычно эмбеддинги не обновляются, но оставим для примера
    embedding: Optional[List[float]] = None 

class Chunk(ChunkBase):
    id: int # int для Pydantic
    embedding: Optional[List[float]] = None

    class Config:
        from_attributes = True 