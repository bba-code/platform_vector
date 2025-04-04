# Platform AI

Приложение для управления векторными базами компаний и ответов на вопросы пользователей с использованием OpenAI.

## Установка

1.  Клонируйте репозиторий:
    ```bash
    git clone <your_repository_url>
    cd platform_vector
    ```
2.  Установите Poetry (если еще не установлен):
    ```bash
    pip install poetry
    ```
3.  Установите зависимости:
    ```bash
    poetry install
    ```
4.  Создайте файл `.env` на основе `.env.example` и заполните переменные окружения.
5.  Запустите приложение с помощью Docker Compose:
    ```bash
    docker-compose up -d
    ```

## API

Документация API доступна по адресу `/docs` после запуска приложения. 