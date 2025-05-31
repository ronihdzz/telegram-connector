from fastapi import APIRouter


index_router = APIRouter(tags=["Index"])

@index_router.get("/")
async def index() -> dict[str, str]:
    return {"message": "Books API 📚"}