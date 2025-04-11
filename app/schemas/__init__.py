from . import company
from . import file
from . import message
from . import request
from . import response
from .request import ProcessFileRequest, MessagePGRequest
from .response import ProcessFileResponse, MessagePGResponse
from .files2 import Files2, Files2Create
from .chunk import Chunk, ChunkCreate, ChunkUpdate

# Опционально: можно импортировать конкретные схемы для удобства,
# но импорта модулей request и response достаточно для исправления ошибки.
# from .company import Company, CompanyCreate, CompanyUpdate
# from .file import File, FileCreate, FileUpdate
# from .message import Message, MessageCreate
# from .request import SetFileRequest
# from .response import SetFileResponse, MessageResponse, ErrorResponse 