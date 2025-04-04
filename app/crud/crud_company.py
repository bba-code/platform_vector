from typing import Optional
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyUpdate

class CRUDCompany(CRUDBase[Company, CompanyCreate, CompanyUpdate]):
    def get_by_platform_id(self, db: Session, *, platform_company_id: int) -> Optional[Company]:
        return db.query(self.model).filter(self.model.platform_company_id == platform_company_id).first()

    def create_with_id(self, db: Session, *, obj_in: CompanyCreate) -> Company:
        # Эта реализация дублирует базовый create, но явно показывает поля.
        # Можно использовать просто self.create(db, obj_in=obj_in)
        db_obj = Company(
            platform_company_id=obj_in.platform_company_id,
            openai_vector_store_id=obj_in.openai_vector_store_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # Другие специфичные для Company CRUD методы можно добавить здесь
    # Например, обновление токена или ID векторной базы
    def update_vector_store_id(self, db: Session, *, db_obj: Company, vector_store_id: str) -> Company:
        db_obj.openai_vector_store_id = vector_store_id
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

company = CRUDCompany(Company) 