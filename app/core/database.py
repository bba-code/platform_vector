from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import settings

# Создаем движок SQLAlchemy напрямую через конструктор, используя параметры из settings
engine = create_engine(
    f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
    pool_pre_ping=True
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей SQLAlchemy
Base = declarative_base()

# Зависимость для получения сессии базы данных в FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()