from openai import OpenAI
import logging
import os
from dotenv import load_dotenv
import time
from typing import Optional, List

# Загружаем переменные окружения из .env файла
load_dotenv()

logger = logging.getLogger(__name__)


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("API-ключ OpenAI не найден в переменных окружения (OPENAI_API_KEY).")
        raise ValueError("Необходимо установить переменную окружения OPENAI_API_KEY")
    return OpenAI(api_key=api_key)


def upload_file(file_path: str, purpose: str = "fine-tune"):
    client = get_openai_client()
    try:
        with open(file_path, "rb") as file:
            uploaded_file = client.files.create(
                file=file,
                purpose=purpose
            )
        logger.info(f"Файл {file_path} успешно загружен. ID: {uploaded_file.id}")
        return uploaded_file.id
    except Exception as e:
        logger.error(f"Ошибка загрузки файла {file_path}: {e}")
        raise

def delete_file(file_id: str):
    client = get_openai_client()
    try:
        client.files.delete(file_id)
        logger.info(f"Файл {file_id} успешно удален")
        return True
    except Exception as e:
        logger.error(f"Ошибка удаления файла {file_id}: {e}")
        raise


def create_vector_store(name: str = ""):
    client = get_openai_client()
    vector_store = client.vector_stores.create(name=name)
    logger.info(f"Создано векторное хранилище: {vector_store.id}")
    return vector_store

def delete_vector_store(vector_store_id: str):
    client = get_openai_client()
    try:
        response = client.vector_stores.delete(vector_store_id=vector_store_id)
        logger.info(f"Векторное хранилище {vector_store_id} успешно удалено.")
        return response
    except Exception as e:
        logger.error(f"Ошибка удаления векторного хранилища {vector_store_id}: {e}")
        raise


def add_file_to_vector_store(vector_store_id: str, file_id: str):
    client = get_openai_client()
    try:
        vector_store_file = client.vector_stores.files.create(
            vector_store_id=vector_store_id,
            file_id=file_id
        )
        logger.info(f"Файл {file_id} добавлен в векторное хранилище {vector_store_id}. ID связи: {vector_store_file.id}")
        return vector_store_file
    except Exception as e:
        logger.error(f"Ошибка добавления файла {file_id} в хранилище {vector_store_id}: {e}")
        raise

def delete_file_from_vector_store(vector_store_id: str, file_id: str):
    client = get_openai_client()
    try:
        deleted_file = client.vector_stores.files.delete(
            vector_store_id=vector_store_id,
            file_id=file_id
        )
        logger.info(f"Файл {file_id} удален из векторного хранилища {vector_store_id}")
        return deleted_file
    except Exception as e:
        logger.error(f"Ошибка удаления файла {file_id} из хранилища {vector_store_id}: {e}")
        raise

def get_prompt_response(prompt: str, vector_store_id: str):
    client = get_openai_client()
    model = "gpt-4o-mini" # Модель задана жестко
    system_instruction = "Ты — полезный ассистент. Ответь на основе предоставленных файлов на вопрос пользователя ниже, отвечай только по данным в файлах, если данных по вопросу нет в файлах напиши что данных нет. Вопрос пользователя:" # Фиксированная инструкция

    # Добавляем системную инструкцию в начало input
    full_input = f"{system_instruction}\n\n{prompt}"
    logger.info("Добавлена фиксированная системная инструкция к input.")

    # Формируем инструмент file_search согласно примеру пользователя
    tools = [{
        "type": "file_search",
        "vector_store_ids": [vector_store_id] # Помещаем ID в список
    }]

    logger.info(f"Запрос к модели {model} с input: '{full_input[:100]}...' и file_search в хранилище {vector_store_id}")

    try:
        # ПРЕДУПРЕЖДЕНИЕ: Метод 'client.responses.create' не является стандартным...
        logger.warning("Вызов нестандартного метода 'client.responses.create' согласно запросу пользователя.")
        if not hasattr(client, 'responses') or not hasattr(client.responses, 'create'):
             logger.error("Атрибут 'client.responses.create' не найден. Этот метод не существует в стандартном API.")
             raise AttributeError("Метод 'client.responses.create' не найден в клиенте OpenAI.")

        response = client.responses.create(
            model=model,
            input=full_input,
            tools=tools
        )
        
        logger.info(f"Получен ответ от модели {model} (метод responses.create).")

        # Парсим ответ для извлечения текста ассистента
        assistant_text = None
        try:
            if response and hasattr(response, 'output') and isinstance(response.output, list):
                for item in response.output:
                     # Ищем сообщение от ассистента
                    if hasattr(item, 'type') and item.type == 'message' and hasattr(item, 'role') and item.role == 'assistant':
                         # Проверяем наличие и тип контента
                        if hasattr(item, 'content') and isinstance(item.content, list) and len(item.content) > 0:
                            first_content = item.content[0]
                            # Ищем текстовый блок
                            if hasattr(first_content, 'type') and first_content.type == 'output_text' and hasattr(first_content, 'text'):
                                assistant_text = first_content.text
                                logger.info("Извлечен текст ответа ассистента.")
                                break # Нашли текст, выходим из цикла
            
            if not assistant_text:
                 logger.warning("Не удалось извлечь текст ответа ассистента из ответа API. Структура ответа не соответствует ожидаемой.")

        except Exception as parse_exc:
            logger.error(f"Ошибка парсинга ответа от OpenAI (метод responses.create): {parse_exc}")
            assistant_text = None # Возвращаем None в случае ошибки парсинга
        
        return assistant_text # Возвращаем извлеченный текст или None

    except AttributeError as e:
         logger.error(f"Ошибка вызова 'client.responses.create': {e}. Этот метод не найден в клиенте OpenAI. Рекомендуется использовать client.chat.completions.create или Assistants API.")
         raise ValueError("Метод 'client.responses.create' не найден в клиенте OpenAI.") from e
    except Exception as e:
        logger.error(f"Ошибка при вызове OpenAI API (метод responses.create): {e}")
        raise

def get_embedding(text: str, model: str = "text-embedding-3-small") -> Optional[List[float]]:
    """
    Генерирует векторное представление (эмбеддинг) для заданного текста.

    Args:
        text: Текст для генерации эмбеддинга.
        model: Модель для генерации эмбеддингов (по умолчанию 'text-embedding-3-small').

    Returns:
        Список чисел (float), представляющий эмбеддинг текста, или None при ошибке.
    """
    client = get_openai_client()
    if not text or not text.strip():
        logger.warning("Получен пустой текст для генерации эмбеддинга.")
        return None
    
    try:
        # Заменяем символы новой строки, т.к. OpenAI их не рекомендует в эмбеддингах
        text = text.replace("\n", " ")
        response = client.embeddings.create(input=[text], model=model) 
        
        # Извлекаем эмбеддинг из ответа
        if response and response.data and len(response.data) > 0:
            embedding = response.data[0].embedding
            logger.info(f"Сгенерирован эмбеддинг размерности {len(embedding)} для текста: '{text[:50]}...' моделью {model}")
            return embedding
        else:
            logger.error(f"Не удалось получить данные эмбеддинга из ответа OpenAI API для модели {model}.")
            return None
    except Exception as e:
        logger.exception(f"Ошибка при генерации эмбеддинга для текста '{text[:50]}...' моделью {model}: {e}")
        return None

def get_prompt_response2(prompt: str, model: str = "gpt-4o-mini") -> Optional[str]:
    """
    Генерирует ответ на промпт с использованием модели чата OpenAI.

    Args:
        prompt: Текст запроса для модели.
        model: Модель чата для использования (по умолчанию 'gpt-4o-mini').

    Returns:
        Строка с ответом от модели или None при ошибке.
    """
    client = get_openai_client()
    system_instruction = "Ты — полезный ассистент. Отвечай на основе предоставленного контекста." # Можно адаптировать
    
    try:
        logger.info(f"Запрос к модели {model} с промптом: '{prompt[:100]}...'")
        
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ]
        )
        
        if completion.choices and len(completion.choices) > 0:
            assistant_response = completion.choices[0].message.content
            logger.info(f"Получен ответ от модели {model}.")
            if assistant_response:
                 return assistant_response.strip()
            else:
                 logger.warning(f"Модель {model} вернула пустой ответ.")
                 return None
        else:
            logger.error(f"Не удалось получить ответ от модели {model}. Ответ API не содержит choices.")
            return None

    except Exception as e:
        logger.exception(f"Ошибка при вызове OpenAI Chat Completions API (модель {model}): {e}")
        return None





