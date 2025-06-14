#!/usr/bin/env python3
"""
🚀 Servidor de desarrollo para Mini Apps de Telegram
Este archivo es opcional - solo para desarrollo local
En producción, usa un servidor web estático (Nginx, CDN, etc.)
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path

# Crear aplicación FastAPI
app = FastAPI(
    title="🚀 Telegram Mini Apps Server",
    description="Servidor de desarrollo para Mini Apps de GymBot",
    version="1.0.0"
)

# Configurar CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directorio de las Mini Apps
WEBAPP_DIR = Path(__file__).parent / "webapp"

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory=WEBAPP_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Página de inicio con lista de Mini Apps disponibles"""
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🚀 Telegram Mini Apps - GymBot</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
                padding: 30px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }
            .apps-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 40px;
            }
            .app-card {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                padding: 24px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                transition: transform 0.3s ease;
            }
            .app-card:hover {
                transform: translateY(-5px);
            }
            .app-icon {
                font-size: 48px;
                margin-bottom: 16px;
            }
            .app-title {
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 12px;
            }
            .app-description {
                opacity: 0.9;
                margin-bottom: 20px;
                line-height: 1.5;
            }
            .app-link {
                display: inline-block;
                background: rgba(255, 255, 255, 0.2);
                color: white;
                text-decoration: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                transition: background 0.3s ease;
            }
            .app-link:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            .info-section {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                padding: 24px;
                backdrop-filter: blur(10px);
                margin-bottom: 20px;
            }
            .code-block {
                background: rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                padding: 16px;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                overflow-x: auto;
                margin: 12px 0;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 Telegram Mini Apps</h1>
            <p>Servidor de desarrollo para GymBot Mini Apps</p>
        </div>

        <div class="apps-grid">
            <div class="app-card">
                <div class="app-icon">🏋️</div>
                <div class="app-title">Rutina Completa</div>
                <div class="app-description">
                    Formulario avanzado para crear rutinas de ejercicio con validación en tiempo real
                    y gestión dinámica de ejercicios.
                </div>
                <a href="/rutina-completa" class="app-link">Abrir Mini App</a>
            </div>

            <div class="app-card">
                <div class="app-icon">👤</div>
                <div class="app-title">Perfil Avanzado</div>
                <div class="app-description">
                    Gestión completa del perfil de usuario con cálculos automáticos de IMC, TMR
                    y calorías diarias.
                </div>
                <a href="/perfil-avanzado" class="app-link">Abrir Mini App</a>
            </div>

            <div class="app-card">
                <div class="app-icon">📝</div>
                <div class="app-title">Registro de Usuario</div>
                <div class="app-description">
                    Formulario elegante y minimalista para registrar nuevos usuarios
                    con validación en tiempo real y animaciones fluidas.
                </div>
                <a href="/registro" class="app-link">Abrir Mini App</a>
            </div>

            <div class="app-card">
                <div class="app-icon">📊</div>
                <div class="app-title">Dashboard</div>
                <div class="app-description">
                    Panel interactivo con estadísticas en tiempo real, progreso semanal
                    y acciones rápidas.
                </div>
                <a href="/dashboard" class="app-link">Abrir Mini App</a>
            </div>
        </div>

        <div class="info-section">
            <h2>🔧 Configuración</h2>
            <p>Para usar estas Mini Apps en tu bot de Telegram:</p>
            
            <h3>1. Configurar URL base:</h3>
            <div class="code-block">
# En src/core/settings/base.py
WEBAPP_BASE_URL: str = "http://localhost:8001"  # Para desarrollo
# WEBAPP_BASE_URL: str = "https://tu-dominio.com"  # Para producción
            </div>

            <h3>2. Comandos del bot:</h3>
            <div class="code-block">
/webapp - Mostrar teclado con Mini Apps
/miniapps - Alias para /webapp
            </div>

            <h3>3. URLs de las Mini Apps:</h3>
            <div class="code-block">
📝 Registro: http://localhost:8001/registro
🏋️ Rutina Completa: http://localhost:8001/rutina-completa
👤 Perfil Avanzado: http://localhost:8001/perfil-avanzado  
📊 Dashboard: http://localhost:8001/dashboard
            </div>
        </div>

        <div class="info-section">
            <h2>🚀 Iniciar servidor</h2>
            <div class="code-block">
# Instalar dependencias
pip install fastapi uvicorn

# Ejecutar servidor
python webapp_server.py

# O con uvicorn directamente
uvicorn webapp_server:app --host 0.0.0.0 --port 8001 --reload
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/registro", response_class=HTMLResponse)
async def registro():
    """Servir Mini App de Registro de Usuario"""
    file_path = WEBAPP_DIR / "registro.html"
    if file_path.exists():
        return FileResponse(file_path, media_type="text/html")
    return HTMLResponse("<h1>❌ Mini App no encontrada</h1><p>Archivo registro.html no existe</p>", status_code=404)

@app.get("/rutina-completa", response_class=HTMLResponse)
async def rutina_completa():
    """Servir Mini App de Rutina Completa"""
    file_path = WEBAPP_DIR / "rutina-completa.html"
    if file_path.exists():
        return FileResponse(file_path, media_type="text/html")
    return HTMLResponse("<h1>❌ Mini App no encontrada</h1><p>Archivo rutina-completa.html no existe</p>", status_code=404)

@app.get("/perfil-avanzado", response_class=HTMLResponse)
async def perfil_avanzado():
    """Servir Mini App de Perfil Avanzado"""
    file_path = WEBAPP_DIR / "perfil-avanzado.html"
    if file_path.exists():
        return FileResponse(file_path, media_type="text/html")
    return HTMLResponse("<h1>❌ Mini App no encontrada</h1><p>Archivo perfil-avanzado.html no existe</p>", status_code=404)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Servir Mini App de Dashboard"""
    file_path = WEBAPP_DIR / "dashboard.html"
    if file_path.exists():
        return FileResponse(file_path, media_type="text/html")
    return HTMLResponse("<h1>❌ Mini App no encontrada</h1><p>Archivo dashboard.html no existe</p>", status_code=404)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "🚀 Telegram Mini Apps Server is running",
        "available_apps": [
            "registro",
            "rutina-completa",
            "perfil-avanzado", 
            "dashboard"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Iniciando servidor de Mini Apps...")
    print("📱 Mini Apps disponibles:")
    print("   📝 http://localhost:8001/registro")
    print("   🏋️ http://localhost:8001/rutina-completa")
    print("   👤 http://localhost:8001/perfil-avanzado")
    print("   📊 http://localhost:8001/dashboard")
    print("\n💡 Panel de control: http://localhost:8001")
    print("\n🔧 Para usar en tu bot, configura:")
    print("   WEBAPP_BASE_URL=http://localhost:8001")
    
    uvicorn.run(
        "webapp_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    ) 