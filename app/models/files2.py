from sqlalchemy import Column, BigInteger, Text
from app.core.database import Base

class Files2(Base):
    __tablename__ = "files2"

    # Используем BigInteger для соответствия int8 в PostgreSQL
    id = Column(BigInteger, primary_key=True, index=True)
    text = Column(Text, nullable=False) 