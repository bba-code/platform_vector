from sqlalchemy import Column, Integer, String, DateTime, func, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    platform_company_id = Column(Integer, nullable=False) # Внешний ключ
    platform_file_id = Column(Integer, index=True, nullable=False) # ID файла на платформе
    file_text = Column(Text, nullable=False) # Содержимое файла
    openai_file_id = Column(Text, nullable=True) # ID файла в OpenAI

    # Отношение (если нужно в будущем)
    # company = relationship("Company", back_populates="files") 