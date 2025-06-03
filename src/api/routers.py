from fastapi import APIRouter
from api.v1.books.endpoints import router as books_endpoints
from api.v1.telegram.endpoints import router as telegram_endpoints

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(books_endpoints)
api_v1_router.include_router(telegram_endpoints)