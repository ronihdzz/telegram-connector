#!/bin/bash

# 🚀 Script de inicio rápido para Telegram Mini Apps
# Autor: FitBot Team
# Descripción: Inicia el servidor de desarrollo para Mini Apps

echo "🚀 Iniciando Telegram Mini Apps Server..."
echo "================================================"

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no está instalado"
    echo "💡 Instala Python3 desde: https://python.org"
    exit 1
fi

# Verificar si pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 no está instalado"
    echo "💡 Instala pip3: sudo apt install python3-pip"
    exit 1
fi

# Crear entorno virtual si no existe
if [ ! -d "venv_miniapps" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv_miniapps
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv_miniapps/bin/activate

# Instalar dependencias
echo "📥 Instalando dependencias..."
pip install fastapi uvicorn python-multipart

# Verificar que existan las Mini Apps
if [ ! -d "webapp" ]; then
    echo "❌ Directorio 'webapp' no encontrado"
    echo "💡 Asegúrate de que los archivos HTML estén en la carpeta 'webapp/'"
    exit 1
fi

# Verificar archivos HTML
missing_files=()
if [ ! -f "webapp/rutina-completa.html" ]; then
    missing_files+=("rutina-completa.html")
fi
if [ ! -f "webapp/perfil-avanzado.html" ]; then
    missing_files+=("perfil-avanzado.html")
fi
if [ ! -f "webapp/dashboard.html" ]; then
    missing_files+=("dashboard.html")
fi

if [ ${#missing_files[@]} -gt 0 ]; then
    echo "⚠️  Archivos faltantes en webapp/:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    echo "💡 Algunas Mini Apps podrían no funcionar correctamente"
fi

# Mostrar información
echo ""
echo "✅ Todo listo para iniciar el servidor"
echo "================================================"
echo "📱 Mini Apps disponibles:"
echo "   🏋️ Rutina Completa: http://localhost:8001/rutina-completa"
echo "   👤 Perfil Avanzado: http://localhost:8001/perfil-avanzado"
echo "   📊 Dashboard: http://localhost:8001/dashboard"
echo ""
echo "💡 Panel de control: http://localhost:8001"
echo "🔧 Health check: http://localhost:8001/health"
echo ""
echo "⚙️  Para usar en tu bot, configura:"
echo "   WEBAPP_BASE_URL=http://localhost:8001"
echo ""
echo "🛑 Para detener el servidor: Ctrl+C"
echo "================================================"
echo ""

# Iniciar servidor
echo "🚀 Iniciando servidor en puerto 8001..."
python3 webapp_server.py 