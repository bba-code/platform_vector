from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
import logging # Добавим логгер для отладки

logger = logging.getLogger(__name__)

# Определяем путь к .env файлу относительно текущего файла (config.py)
# config.py находится в app/core/, .env - в корне
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
logger.info(f"Попытка загрузки .env из: {dotenv_path}")

# Загружаем переменные окружения из файла .env, явно указывая путь и кодировку
loaded = load_dotenv(dotenv_path=dotenv_path, encoding='utf-8')
logger.info(f"Результат load_dotenv: {loaded}")

# Отладка: выведем значение переменной сразу после загрузки
db_url_from_os = os.getenv("DATABASE_URL")
logger.debug(f"DATABASE_URL из os.getenv сразу после load_dotenv: {db_url_from_os!r}")

class Settings(BaseSettings):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Platform AI")
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")

    # Отдельные параметры подключения к базе данных
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "")

    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_ASSISTANT_ID: str = os.getenv("OPENAI_ASSISTANT_ID", "")

    class Config:
        case_sensitive = True
        # Если вы не используете Docker и .env файл лежит в корне проекта
        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings()
logger.debug(f"DB_USER: {settings.DB_USER}")
logger.debug(f"DB_HOST: {settings.DB_HOST}")
logger.debug(f"DB_PORT: {settings.DB_PORT}")
logger.debug(f"DB_NAME: {settings.DB_NAME}")
# Не логируем пароль в целях безопасности 