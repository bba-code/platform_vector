from sqlalchemy import Column, BigInteger, Text, ForeignKey
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector # Импортируем тип Vector

from app.core.database import Base

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(BigInteger, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    index = Column(BigInteger, nullable=False) # Порядковый номер чанка (int8)
    file_id = Column(BigInteger, ForeignKey("files2.id"), nullable=False) # Связь с файлом (int8)
    embedding = Column(Vector(1536), nullable=True) # Векторное представление (1536 измерений)

    # Опционально: связь для удобного доступа к файлу из чанка
    file = relationship("Files2") 