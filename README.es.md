# 🤖 Telegram Connector

**Language / Idioma:**
* [English](README.md) 
* [Español](README.es.md)

---

| Entorno CI | Cobertura |
|-----------|----------|
| development| ![Coverage Badge](https://github.com/ronihdzz/telegram-connector/blob/artifacts/development/latest/coverage.svg) 


## 📋 Descripción

**Telegram Connector** es una solución integral que permite a las aplicaciones integrarse seamlessly con bots de Telegram, habilitando tanto la **recepción de mensajes entrantes** como el **envío de mensajes salientes** a través de cualquier bot registrado en la plataforma.

### ✨ Características Principales

- 🔄 **Comunicación Bidireccional**: Recibe y envía mensajes desde/hacia Telegram
- 🎯 **Multi-Bot Support**: Gestiona múltiples bots por usuario
- 📡 **Webhooks Automatizados**: Configuración automática de webhooks con Telegram
- 🛡️ **Autenticación Robusta**: Validación de API Keys y secret tokens
- 📊 **Logging Detallado**: Trazabilidad completa de mensajes y operaciones
- 🐳 **Docker Ready**: Despliegue containerizado con docker-compose

## 🏗️ Arquitectura del Sistema

### Flujo de Datos

```mermaid
sequenceDiagram
    participant User as "Usuario/Sistema"
    participant API as "API REST"
    participant DB as "PostgreSQL"
    participant TG as "API Telegram" 
    participant Bot as "Bot Telegram"
    participant Webhook as "Sistema Destino"
    
    Note over User,Webhook: Flujo de Registro de Bot
    User->>+API: POST /v1/telegram/connect<br/>(bot_user_name, bot_token)
    API->>+DB: Crear TelegramConnector<br/>(credenciales + secret_token)
    DB->>-API: Conector creado
    API->>+TG: setWebhook<br/>(webhook_url + secret_token)
    TG->>-API: Webhook configurado
    API->>-User: Conector registrado exitosamente
    
    Note over User,Webhook: Flujo de Mensaje Entrante
    Bot->>+TG: Usuario envía mensaje al bot
    TG->>+API: POST /v1/telegram/webhook/{id}<br/>(mensaje + secret_token)
    API->>+DB: Validar conector por ID
    DB->>-API: Conector válido
    API->>API: Procesar mensaje<br/>(extraer texto, chat_id, etc.)
    API->>+Webhook: POST webhook_url<br/>(mensaje procesado)
    Webhook->>-API: Mensaje recibido
    API->>-TG: Status OK
    
    Note over User,Webhook: Flujo de Mensaje Saliente
    User->>+API: POST /v1/telegram/send/{id}<br/>(chat_id, text)
    API->>+DB: Validar conector y permisos
    DB->>-API: Conector válido
    API->>+TG: sendMessage<br/>(bot_token, chat_id, text)
    TG->>+Bot: Entregar mensaje al usuario
    Bot->>-TG: Mensaje entregado
    TG->>-API: message_id de confirmación
    API->>-User: Mensaje enviado exitosamente
```

### Componentes del Sistema

#### 🎯 Capa API (`api/v1/telegram/`)
- **endpoints.py**: Exposición de APIs REST para operaciones de Telegram
- **services.py**: Lógica de negocio para conectar, enviar y recibir mensajes
- **repositories.py**: Capa de acceso a datos para operaciones CRUD
- **schema.py**: Modelos de datos y validación con Pydantic

#### 🗄️ Capa de Datos (`db/postgres/`)
- **telegram_connectors.py**: Modelo de base de datos para gestión de bots

## 📊 Modelo de Datos

### TelegramConnector

Tabla principal que almacena la información de los bots conectados:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | Identificador único del conector |
| `user_id` | UUID | ID del usuario propietario del bot |
| `bot_user_name` | String | Nombre de usuario del bot (@ejemplo_bot) |
| `bot_token` | String | Token de API del bot |
| `bot_token_secret` | String | Token secreto para validación de webhooks |
| `created_at` | DateTime | Fecha de creación |
| `updated_at` | DateTime | Fecha de última actualización |

## 🔌 Endpoints de la API

### 1. Conectar Bot de Telegram

**`POST /v1/telegram/connect`**

Registra un nuevo bot de Telegram y configura su webhook automáticamente.

**Headers:**
```json
{
  "X-Api-Key": "tu_api_key_aqui",
  "X-User-Id": "uuid_del_usuario"
}
```

**Request Body:**
```json
{
  "bot_user_name": "@mi_bot",
  "bot_token": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "bot_user_name": "@mi_bot",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

### 2. Webhook para Mensajes Entrantes

**`POST /v1/telegram/webhook/{telegram_connector_id}`**

Endpoint automáticamente configurado por Telegram para recibir mensajes. Telegram envía un objeto `Update` completo en el body del request.

**Headers:**
```json
{
  "Content-Type": "application/json",
  "X-Telegram-Bot-Api-Secret-Token": "token_secreto_generado"
}
```

**Request Body (enviado por Telegram):**
```json
{
  "update_id": 10000,
  "message": {
    "message_id": 1365,
    "date": 1441645532,
    "chat": {
      "id": 1111111,
      "type": "private",
      "first_name": "Test",
      "last_name": "Test Lastname",
      "username": "Test"
    },
    "from": {
      "id": 1111111,
      "is_bot": false,
      "first_name": "Test",
      "last_name": "Test Lastname",
      "username": "Test"
    },
    "text": "¡Hola desde Telegram!"
  }
}
```

**Response:**
```json
{
  "status": "ok"
}
```

### 3. Enviar Mensaje

**`POST /v1/telegram/send/{telegram_connector_id}`**

Envía un mensaje a través del bot especificado.

**Headers:**
```json
{
  "X-Api-Key": "tu_api_key_aqui",
  "X-User-Id": "uuid_del_usuario"
}
```

**Request Body:**
```json
{
  "chat_id": 123456789,
  "text": "¡Hola! Este es un mensaje desde la API"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "telegram_message_id": 987654321,
    "status": "sent"
  }
}
```

## ⚙️ Variables de Entorno

### Variables Requeridas

```bash
# Configuración General
ENVIRONMENT=local                              # Entorno de ejecución
HOST=http://localhost:8000                     # URL base de la API
API_KEY=tu_api_key_super_secreto              # Clave API para autenticación

# Base de Datos
POSTGRESQL_URL=postgresql://user:password@localhost:5432/telegram_connector

# Webhook de Destino
WEBHOOK_MESSAGE_RECEIVED=https://tu-app.com/api/webhook/telegram-message
```

### Variables Opcionales

```bash
# Logging y Monitoreo
SENTRY_DSN=https://tu-sentry-dsn.com           # Para tracking de errores
TIME_ZONE=America/Mexico_City                  # Zona horaria

# Configuración del Proyecto
PROJECT__NAME=Telegram Connector
PROJECT__VERSION=1.0.0
PROJECT__DESCRIPTION=API para integración con Telegram
```

## 🚀 Instalación y Configuración

### Prerrequisitos

- Python 3.12+
- PostgreSQL
- Docker y Docker Compose (opcional)

### Instalación con Poetry

1. **Clonar el repositorio:**
```bash
git clone https://github.com/ronihdzz/telegram-connector.git
cd telegram-connector
```

2. **Instalar dependencias:**
```bash
poetry install
```

3. **Configurar variables de entorno:**
```bash
cp .envs/.example.env .envs/.local.env
# Editar .envs/.local.env con tu configuración
```

4. **Ejecutar la aplicación:**
```bash
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Instalación con Docker

1. **Clonar y ejecutar:**
```bash
git clone https://github.com/ronihdzz/telegram-connector.git
cd telegram-connector
docker-compose up -d
```

## 📖 Ejemplos de Uso

### 1. Registrar un Bot

```python
import requests

# Configuración
API_BASE = "http://localhost:8000/v1"
API_KEY = "tu_api_key"
USER_ID = "550e8400-e29b-41d4-a716-446655440001"

# Registrar bot
response = requests.post(
    f"{API_BASE}/telegram/connect",
    headers={
        "X-Api-Key": API_KEY,
        "X-User-Id": USER_ID
    },
    json={
        "bot_user_name": "@mi_bot_de_prueba",
        "bot_token": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
    }
)

bot_data = response.json()
connector_id = bot_data["data"]["id"]
print(f"Bot registrado con ID: {connector_id}")
```

### 2. Enviar un Mensaje

```python
# Enviar mensaje usando el bot registrado
response = requests.post(
    f"{API_BASE}/telegram/send/{connector_id}",
    headers={
        "X-Api-Key": API_KEY,
        "X-User-Id": USER_ID
    },
    json={
        "chat_id": 123456789,  # ID del chat destino
        "text": "¡Hola desde mi aplicación!"
    }
)

result = response.json()
print(f"Mensaje enviado con ID: {result['data']['telegram_message_id']}")
```

### 3. Configurar Webhook de Destino

Para recibir mensajes entrantes, configura un endpoint en tu aplicación:

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/api/webhook/telegram-message")
async def receive_telegram_message(request: Request):
    """
    Webhook que recibe mensajes entrantes de Telegram
    """
    data = await request.json()
    
    print(f"Mensaje recibido de {data['bot_user_name']}")
    print(f"Chat ID: {data['chat_id']}")
    print(f"Texto: {data['text']}")
    print(f"Usuario: {data['user_id']}")
    
    # Procesar el mensaje aquí...
    
    return {"status": "processed"}
```

## 📚 Documentación Adicional

### Documentación de la API

Una vez ejecutándose la aplicación, accede a:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Estructura del Proyecto

```
telegram-connector/
├── src/
│   ├── api/v1/telegram/          # Endpoints de la API REST
│   ├── db/postgres/models/       # Modelos de base de datos
│   ├── core/settings/            # Configuración de la aplicación
│   ├── shared/                   # Utilidades compartidas
│   └── tests/                    # Suites de pruebas
├── docker_images/                # Configuraciones Docker
├── .envs/                        # Variables de entorno
└── docs/                         # Documentación adicional
```

## 🧪 Pruebas

Ejecutar la suite de pruebas:

```bash
# Con Poetry
poetry run pytest

# Con cobertura
poetry run pytest --cov=src --cov-report=html
```

## 🤝 Contribuciones

1. Haz fork del proyecto
2. Crea tu rama de feature (`git checkout -b feature/CaracteristicaIncreible`)
3. Confirma tus cambios (`git commit -m 'Agregar alguna CaracteristicaIncreible'`)
4. Sube a la rama (`git push origin feature/CaracteristicaIncreible`)
5. Abre un Pull Request


## 👨‍💻 Autor

**Ronaldo Hernández** - [@ronihdzz](https://github.com/ronihdzz)

---

<div align="center">

**¿Te gusta el proyecto? ¡Dale una ⭐!**

[🐛 Reportar Bug](https://github.com/ronihdzz/telegram-connector/issues) • [✨ Solicitar Feature](https://github.com/ronihdzz/telegram-connector/issues) • [💬 Discusiones](https://github.com/ronihdzz/telegram-connector/discussions)

</div> 