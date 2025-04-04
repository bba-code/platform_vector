from sqlalchemy import Column, Integer, String, DateTime, func, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    text = Column(Text, nullable=False)
    user_type = Column(String, nullable=False) # "user" или "ai"
    platform_user_id = Column(Integer, index=True, nullable=False)
    platform_company_id = Column(Integer, nullable=False) # Внешний ключ

    # Отношение (если нужно в будущем)
    # company = relationship("Company", back_populates="messages") 