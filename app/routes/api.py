from fastapi import APIRouter

from app.routes.endpoints import files, messages, filespg, messagespg

api_router = APIRouter()

# Подключаем роутеры эндпоинтов
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"]) 
api_router.include_router(filespg.router, prefix="/filespg", tags=["filespg"]) 
api_router.include_router(messagespg.router, prefix="/messagespg", tags=["messagespg"]) 