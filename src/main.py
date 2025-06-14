from core.settings import settings
from fastapi import FastAPI
from mangum import Mangum
from fastapi.openapi.utils import get_openapi
import os
from api.routers import api_v1_router
from api.endpoints import index_router
from typing import Any
from core.settings import settings
from shared.middlewares import (
    CatcherExceptions,
    CatcherExceptionsPydantic
)
from fastapi.middleware import Middleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI(
    title=settings.PROJECT.NAME,
    version=settings.PROJECT.VERSION,
    description=settings.PROJECT.DESCRIPTION,
    root_path=settings.ROOT_PATH,
    middleware=[
        Middleware(CatcherExceptions)
    ]
)


def custom_openapi() -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["openapi"] = "3.0.3"
    openapi_schema["servers"] = [{"url": settings.ROOT_PATH}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi # type: ignore
app.include_router(api_v1_router)
app.include_router(index_router)
CatcherExceptionsPydantic(app)
handler = Mangum(app)

# 🚀 INTEGRAR MINI APPS EN EL MISMO FASTAPI
webapp_dir = Path(__file__).parent.parent / "webapp"

# Montar archivos estáticos de Mini Apps
app.mount("/webapp", StaticFiles(directory=webapp_dir), name="webapp")

# Opcional: Rutas específicas para mejor SEO
@app.get("/rutina-completa", response_class=HTMLResponse)
async def rutina_completa_redirect():
    return RedirectResponse(url="/webapp/rutina-completa.html")

@app.get("/perfil-avanzado", response_class=HTMLResponse) 
async def perfil_avanzado_redirect():
    return RedirectResponse(url="/webapp/perfil-avanzado.html")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_redirect():
    return RedirectResponse(url="/webapp/dashboard.html")

@app.get("/registro", response_class=HTMLResponse)
async def registro_redirect():
    return RedirectResponse(url="/webapp/registro.html")


# Configuración en settings.py sería:
# WEBAPP_BASE_URL: str = "https://tu-dominio.com/webapp"
