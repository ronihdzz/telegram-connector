# 🚀 Telegram Mini Apps - FitBot

## 📱 **¿Qué son las Mini Apps?**

Las **Telegram Mini Apps** (también conocidas como Web Apps) son aplicaciones web que se ejecutan directamente dentro de Telegram, proporcionando una experiencia nativa y fluida sin necesidad de salir del chat.

## 🎯 **Características Principales**

### ✨ **Experiencia Nativa**
- **Integración completa** con el tema de Telegram
- **Botones nativos** (MainButton, BackButton)
- **Transiciones suaves** y animaciones
- **Responsive design** para todos los dispositivos

### 🔒 **Seguridad**
- **Autenticación automática** con datos de usuario de Telegram
- **Comunicación segura** con el bot
- **Validación de datos** en tiempo real

### 🎨 **Diseño Profesional**
- **Tema adaptativo** que sigue los colores de Telegram
- **Interfaz moderna** con gradientes y sombras
- **Iconos emoji** para mejor UX
- **Animaciones CSS** suaves

## 📂 **Mini Apps Disponibles**

### 🏋️ **1. Rutina Completa** (`rutina-completa.html`)
**Funcionalidades:**
- ✅ Formulario completo para crear rutinas
- ✅ Agregar/eliminar ejercicios dinámicamente
- ✅ Validación en tiempo real
- ✅ Cálculo automático de estadísticas
- ✅ Envío de datos estructurados al bot

**Campos:**
- Nombre de la rutina
- Objetivo (fuerza, hipertrofia, etc.)
- Duración estimada
- Lista de ejercicios con series/repeticiones

### 👤 **2. Perfil Avanzado** (`perfil-avanzado.html`)
**Funcionalidades:**
- ✅ Información básica (nombre, edad, género)
- ✅ Datos físicos (peso, altura, objetivos)
- ✅ Cálculo automático de IMC, TMR y calorías
- ✅ Selección múltiple de áreas de enfoque
- ✅ Nivel de experiencia fitness

**Cálculos automáticos:**
- **IMC** (Índice de Masa Corporal)
- **TMR** (Tasa Metabólica en Reposo)
- **Calorías diarias** según nivel de actividad

### 📊 **3. Dashboard** (`dashboard.html`)
**Funcionalidades:**
- ✅ Estadísticas en tiempo real
- ✅ Progreso semanal con barras visuales
- ✅ Acciones rápidas interactivas
- ✅ Historial de actividad reciente
- ✅ Botón flotante para acceso rápido

**Métricas mostradas:**
- Rutinas completadas
- Días activos
- Tiempo total de entrenamiento
- Calorías quemadas

## ⚙️ **Configuración**

### 1. **Configurar URL Base**
En `src/core/settings/base.py`:
```python
WEBAPP_BASE_URL: str = "https://tu-dominio.com/webapp"
```

### 2. **Servir las Mini Apps**
Las Mini Apps deben estar accesibles vía HTTPS. Opciones:

#### **Opción A: Servidor Web Estático**
```bash
# Nginx, Apache, o cualquier servidor web
# Servir la carpeta webapp/ en tu dominio
```

#### **Opción B: CDN (Recomendado)**
```bash
# Subir archivos a:
# - GitHub Pages
# - Netlify
# - Vercel
# - AWS S3 + CloudFront
```

#### **Opción C: Integrar en FastAPI**
```python
# En tu aplicación FastAPI
from fastapi.staticfiles import StaticFiles

app.mount("/webapp", StaticFiles(directory="webapp"), name="webapp")
```

### 3. **Variables de Entorno**
```bash
# .env
WEBAPP_BASE_URL=https://tu-dominio.com/webapp
BOT_MANAGER_TOKEN=tu_bot_token
BOT_MANAGER_SECRET=tu_secret_token
```

## 🚀 **Uso en el Bot**

### **Activar Mini Apps**
```python
# El usuario escribe:
/webapp
# o
/miniapps
```

### **Teclado con Mini Apps**
```python
keyboard = {
    "keyboard": [
        [{
            "text": "🏋️ Rutina Completa", 
            "web_app": {"url": f"{WEBAPP_BASE_URL}/rutina-completa.html"}
        }],
        [{
            "text": "👤 Perfil Avanzado", 
            "web_app": {"url": f"{WEBAPP_BASE_URL}/perfil-avanzado.html"}
        }],
        [{
            "text": "📊 Dashboard", 
            "web_app": {"url": f"{WEBAPP_BASE_URL}/dashboard.html"}
        }]
    ],
    "resize_keyboard": True
}
```

## 📡 **Flujo de Datos**

### **1. Usuario abre Mini App**
```
Usuario toca botón → Telegram abre WebView → Mini App se carga
```

### **2. Usuario completa formulario**
```
Formulario → Validación JS → Datos JSON → tg.sendData()
```

### **3. Bot recibe datos**
```python
# En webhook_manager
if message.get("web_app_data"):
    data = json.loads(message["web_app_data"]["data"])
    # Procesar según data["type"]
```

### **4. Respuesta al usuario**
```
Bot procesa → Envía confirmación → Mini App se cierra
```

## 🔧 **Estructura de Datos**

### **Rutina Completa**
```json
{
    "type": "rutina_completa",
    "rutina": {
        "nombre": "Rutina de Pecho",
        "objetivo": "hipertrofia",
        "duracion": "60min",
        "ejercicios": [
            {
                "nombre": "Press de banca",
                "series": 4,
                "repeticiones": 12,
                "peso": "80kg"
            }
        ],
        "fecha_creacion": "2024-01-15T10:30:00Z"
    }
}
```

### **Perfil Avanzado**
```json
{
    "type": "perfil_avanzado",
    "perfil": {
        "nombre": "Juan Pérez",
        "edad": 28,
        "peso": 75.5,
        "altura": 180,
        "objetivo_principal": "ganar_musculo",
        "imc": 23.3,
        "tmr": 1850,
        "calorias_diarias": 2590
    }
}
```

### **Dashboard**
```json
{
    "type": "dashboard_action",
    "action": "exportar_datos",
    "details": {
        "formato": "json",
        "incluir_historial": true
    }
}
```

## 🎨 **Personalización**

### **Colores del Tema**
Las Mini Apps usan automáticamente los colores del tema de Telegram:
```css
/* Variables CSS automáticas */
var(--tg-theme-bg-color)           /* Fondo principal */
var(--tg-theme-text-color)         /* Texto principal */
var(--tg-theme-button-color)       /* Color de botones */
var(--tg-theme-button-text-color)  /* Texto de botones */
var(--tg-theme-secondary-bg-color) /* Fondo secundario */
var(--tg-theme-hint-color)         /* Texto secundario */
```

### **Responsive Design**
```css
@media (max-width: 480px) {
    /* Adaptaciones para móvil */
    .grid { grid-template-columns: 1fr; }
}
```

## 🔍 **Debugging**

### **Console Logs**
```javascript
console.log('Mini App cargada correctamente');
console.log('Datos enviados:', data);
```

### **Telegram Web App Debug**
```javascript
// Información de debug
console.log('initData:', tg.initData);
console.log('user:', tg.initDataUnsafe.user);
console.log('theme:', tg.themeParams);
```

### **Validación de Datos**
```javascript
// Validar antes de enviar
if (!formData.nombre) {
    throw new Error('Nombre es requerido');
}
```

## 🚨 **Troubleshooting**

### **Mini App no carga**
- ✅ Verificar HTTPS en la URL
- ✅ Comprobar CORS headers
- ✅ Validar certificado SSL

### **Datos no se envían**
- ✅ Verificar `tg.sendData()` syntax
- ✅ Comprobar JSON válido
- ✅ Revisar webhook handler

### **Tema no se aplica**
- ✅ Verificar variables CSS `--tg-theme-*`
- ✅ Comprobar `tg.ready()` llamado
- ✅ Validar fallbacks en CSS

## 📚 **Recursos Adicionales**

- [Telegram Web Apps Documentation](https://core.telegram.org/bots/webapps)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [CSS Variables for Theming](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)

## 🎉 **¡Listo para usar!**

Con esta implementación tienes:
- ✅ **3 Mini Apps** completamente funcionales
- ✅ **Integración nativa** con Telegram
- ✅ **Diseño profesional** y responsive
- ✅ **Validación completa** de datos
- ✅ **Manejo de errores** robusto

¡Tu bot ahora tiene la experiencia más avanzada posible en Telegram! 🚀 