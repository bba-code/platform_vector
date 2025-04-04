from .base import Base # Базовый класс для моделей

# Импортируем все модели, чтобы SQLAlchemy (и Alembic в будущем) мог их обнаружить
from .company import Company
from .file import File
from .message import Message 