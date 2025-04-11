from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text # Для использования SQL функций
from pgvector.sqlalchemy import Vector # Для типизации вектора

from app.crud.base import CRUDBase
from app.models.chunk import Chunk
from app.schemas.chunk import ChunkCreate, ChunkUpdate

class CRUDChunk(CRUDBase[Chunk, ChunkCreate, ChunkUpdate]):
    
    def create_multi(self, db: Session, *, objs_in: List[ChunkCreate]) -> List[Chunk]:
        """Создает несколько чанков одним коммитом."""
        # Преобразуем Pydantic схемы в данные для модели SQLAlchemy
        db_objs_data = [obj.model_dump() for obj in objs_in] # Используем model_dump() для Pydantic V2
        db_objs = [Chunk(**data) for data in db_objs_data]
        
        db.add_all(db_objs)
        db.commit()
        # Не делаем refresh для каждого объекта для производительности
        # Вместо этого можно вернуть ID созданных чанков, если нужно
        return db_objs # Возвращаем созданные объекты

    def get_multi_by_file_id(self, db: Session, *, file_id: int, skip: int = 0, limit: int = 1000) -> List[Chunk]:
        """Получает чанки для конкретного файла."""
        return db.query(self.model).filter(self.model.file_id == file_id).offset(skip).limit(limit).all()

    def get_similar_chunks(self, db: Session, *, query_embedding: List[float], file_ids: Optional[List[int]] = None, limit: int = 5) -> List[Chunk]:
        """Находит чанки, наиболее похожие на заданный эмбеддинг запроса.
        Если передан список file_ids, ищет только в пределах этих файлов.
        Если file_ids не передан или пуст, ищет по ВСЕМ чанкам.
        Использует косинусное расстояние (<=>).
        """
        
        params = {
            "query_vec": str(query_embedding), # pgvector ожидает вектор в виде строки
            "limit": limit
        }
        
        # Базовая часть запроса
        sql_query = """
            SELECT id, text, index, file_id, embedding 
            FROM chunks
            WHERE embedding IS NOT NULL 
        """
        
        # Добавляем фильтр по file_id, если он предоставлен и не пуст
        if file_ids: # Проверяем, что список не None и не пустой
            file_ids_tuple = tuple(file_ids)
            sql_query += " AND file_id IN :file_ids "
            params["file_ids"] = file_ids_tuple
        # Иначе фильтра по file_id не будет

        # Добавляем сортировку и лимит
        sql_query += " ORDER BY embedding <=> CAST(:query_vec AS vector) LIMIT :limit "
        
        query = text(sql_query)

        # Выполняем "сырой" SQL запрос, но получаем ORM объекты
        results = db.query(Chunk).from_statement(query).params(**params).all()
        
        return results

chunk = CRUDChunk(Chunk) 