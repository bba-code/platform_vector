from typing import List
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.message import Message
from app.schemas.message import MessageCreate, MessageUpdate

class CRUDMessage(CRUDBase[Message, MessageCreate, MessageUpdate]):
    def create_message(self, db: Session, *, obj_in: MessageCreate) -> Message:
        # Явное создание для наглядности
        db_obj = Message(
            text=obj_in.text,
            user_type=obj_in.user_type,
            platform_user_id=obj_in.platform_user_id,
            platform_company_id=obj_in.platform_company_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_history_for_user_company(
        self, db: Session, *, platform_company_id: int, platform_user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Message]:
        return (
            db.query(self.model)
            .filter(
                self.model.platform_company_id == platform_company_id,
                self.model.platform_user_id == platform_user_id
            )
            .order_by(self.model.created_at.desc()) # Сначала последние сообщения
            .offset(skip)
            .limit(limit)
            .all()
        )

message = CRUDMessage(Message) 