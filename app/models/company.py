from sqlalchemy import Column, Integer, String, DateTime, func, Text
from sqlalchemy.orm import relationship

from app.core.database import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    platform_company_id = Column(Integer, unique=True, index=True, nullable=False)
    openai_vector_store_id = Column(Text, nullable=True) # ID векторной базы в OpenAI

    # Отношения (если нужны в будущем)
    # files = relationship("File", back_populates="company")
    # messages = relationship("Message", back_populates="company") 