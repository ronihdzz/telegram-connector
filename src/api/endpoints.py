from fastapi import APIRouter
from core.settings import settings

index_router = APIRouter(tags=["Index"])

@index_router.get("/")
async def index() -> dict[str, str]:
    return {"message": f"{settings.PROJECT.NAME}"}