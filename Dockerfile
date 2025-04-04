# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем Poetry
RUN pip install poetry

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY pyproject.toml poetry.lock ./

# Устанавливаем зависимости проекта, не включая dev зависимости
RUN poetry config virtualenvs.create false && poetry install --no-root --no-dev

# Копируем остальную часть приложения
COPY ./app /app/app

# Открываем порт 8020
EXPOSE 8020

# Команда для запуска приложения на порту 8020
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8020"] 