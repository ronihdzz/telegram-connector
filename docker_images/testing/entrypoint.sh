#!/bin/sh
set -e

echo "📦 Running entrypoint.sh..."

# 🧬 Cargar variables si el archivo existe
if [ -f ./ci.env.sh ]; then
  echo "📦 Running ci.env.sh..."
  . ./ci.env.sh
else
  echo "⚠️ No ci.env.sh found. Skipping..."
fi

# 🗂️ Asegurar que la carpeta de reportes exista
mkdir -p reports
echo "📁 Reports directory created/verified at: $(pwd)/reports"

# 🧪 Ejecutar tests con coverage
echo "🧪 Running tests with coverage..."
poetry run coverage run -m pytest src/tests -s -v --lf --junitxml=reports/unittest_report.xml

# 📄 Generar reportes de cobertura
echo "📊 Generating coverage reports..."
poetry run coverage xml -o reports/coverage.xml
poetry run coverage report

# 🖼️ Generar badge en SVG
echo "🎨 Generating coverage badge..."
poetry run coverage-badge -o reports/coverage.svg

# Verificar que los archivos existan antes de copiarlos
echo "🔍 Verificando que los archivos de reporte existan:"
ls -la reports/

# 📤 Copiar archivos seleccionados a /app/coverage-reports/
echo "📤 Copiando reportes a /app/coverage-reports/"
mkdir -p /app/coverage-reports/
echo "📁 Directorio de destino creado: /app/coverage-reports/"

# Copiar coverage.xml con verificación
if [ -f reports/coverage.xml ]; then
  cp reports/coverage.xml /app/coverage-reports/
  echo "✅ coverage.xml copiado exitosamente"
else
  echo "❌ reports/coverage.xml no existe!"
fi

# Copiar coverage.svg con verificación
if [ -f reports/coverage.svg ]; then
  cp reports/coverage.svg /app/coverage-reports/
  echo "✅ coverage.svg copiado exitosamente"
else
  echo "❌ reports/coverage.svg no existe!"
fi

# Copiar unittest_report.xml con verificación
if [ -f reports/unittest_report.xml ]; then
  cp reports/unittest_report.xml /app/coverage-reports/
  echo "✅ unittest_report.xml copiado exitosamente"
else
  echo "❌ reports/unittest_report.xml no existe!"
fi

# Mostrar el contenido de la carpeta de destino
echo "📋 Contenido de /app/coverage-reports/:"
ls -la /app/coverage-reports/

echo "✅ Entrypoint complete."
