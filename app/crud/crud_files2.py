from app.crud.base import CRUDBase
from app.models.files2 import Files2 # SQLAlchemy модель
# Переименовываем импортируемую Pydantic схему, чтобы избежать конфликта
from app.schemas.files2 import Files2Create, Files2 as Files2Schema 

# Используем модель Files2 и схему Files2Schema в качестве UpdateSchemaType
class CRUDFiles2(CRUDBase[Files2, Files2Create, Files2Schema]):
    pass

# Передаем SQLAlchemy модель в конструктор
files2 = CRUDFiles2(Files2) 