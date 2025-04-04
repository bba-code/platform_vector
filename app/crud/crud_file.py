from typing import Optional, List
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.file import File
from app.schemas.file import FileCreate, FileUpdate

class CRUDFile(CRUDBase[File, FileCreate, FileUpdate]):
    def get_by_platform_ids(self, db: Session, *, platform_company_id: int, platform_file_id: int) -> Optional[File]:
        return db.query(self.model)\
            .filter(self.model.platform_company_id == platform_company_id, self.model.platform_file_id == platform_file_id)\
            .first()

    def get_multi_by_company(self, db: Session, *, platform_company_id: int, skip: int = 0, limit: int = 100) -> List[File]:
        return db.query(self.model)\
            .filter(self.model.platform_company_id == platform_company_id)\
            .offset(skip)\
            .limit(limit)\
            .all()

    def update_openai_id(self, db: Session, *, db_obj: File, openai_file_id: str) -> File:
        db_obj.openai_file_id = openai_file_id
        # updated_at обновится автоматически благодаря onupdate=func.now() в модели
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

file = CRUDFile(File) 