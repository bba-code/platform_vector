from pydantic import BaseModel

class Files2Base(BaseModel):
    text: str

class Files2Create(Files2Base):
    pass

class Files2(Files2Base):
    id: int # Используем int, Pydantic обработает BigInt

    class Config:
        from_attributes = True 