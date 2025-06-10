# 🤖 Telegram Connector

**Language / Idioma:**
* [English](README.md) 
* [Español](README.es.md)

---

| CI Environment | Coverage |
|-----------|----------|
| development| ![Coverage Badge](https://github.com/ronihdzz/telegram-connector/blob/artifacts/development/latest/coverage.svg) 


## 📋 Description

**Telegram Connector** is a comprehensive solution that allows applications to seamlessly integrate with Telegram bots, enabling both **incoming message reception** and **outgoing message sending** through any bot registered on the platform.

### ✨ Key Features

- 🔄 **Bidirectional Communication**: Receive and send messages from/to Telegram
- 🎯 **Multi-Bot Support**: Manage multiple bots per user
- 📡 **Automated Webhooks**: Automatic webhook configuration with Telegram
- 🛡️ **Robust Authentication**: API Keys and secret tokens validation
- 📊 **Detailed Logging**: Complete traceability of messages and operations
- 🐳 **Docker Ready**: Containerized deployment with docker-compose

## 🏗️ System Architecture

### Data Flow

```mermaid
sequenceDiagram
    participant User as "User/System"
    participant API as "REST API"
    participant DB as "PostgreSQL"
    participant TG as "Telegram API" 
    participant Bot as "Telegram Bot"
    participant Webhook as "Target System"
    
    Note over User,Webhook: Bot Registration Flow
    User->>+API: POST /v1/telegram/connect<br/>(bot_user_name, bot_token)
    API->>+DB: Create TelegramConnector<br/>(credentials + secret_token)
    DB->>-API: Connector created
    API->>+TG: setWebhook<br/>(webhook_url + secret_token)
    TG->>-API: Webhook configured
    API->>-User: Connector registered successfully
    
    Note over User,Webhook: Incoming Message Flow
    Bot->>+TG: User sends message to bot
    TG->>+API: POST /v1/telegram/webhook/{id}<br/>(message + secret_token)
    API->>+DB: Validate connector by ID
    DB->>-API: Valid connector
    API->>API: Process message<br/>(extract text, chat_id, etc.)
    API->>+Webhook: POST webhook_url<br/>(processed message)
    Webhook->>-API: Message received
    API->>-TG: Status OK
    
    Note over User,Webhook: Outgoing Message Flow
    User->>+API: POST /v1/telegram/send/{id}<br/>(chat_id, text)
    API->>+DB: Validate connector and permissions
    DB->>-API: Valid connector
    API->>+TG: sendMessage<br/>(bot_token, chat_id, text)
    TG->>+Bot: Deliver message to user
    Bot->>-TG: Message delivered
    TG->>-API: message_id confirmation
    API->>-User: Message sent successfully
```

### System Components

#### 🎯 API Layer (`api/v1/telegram/`)
- **endpoints.py**: REST API exposure for Telegram operations
- **services.py**: Business logic for connecting, sending and receiving messages
- **repositories.py**: Data access layer for CRUD operations
- **schema.py**: Data models and validation with Pydantic

#### 🗄️ Data Layer (`db/postgres/`)
- **telegram_connectors.py**: Database model for bot management

## 📊 Data Model

### TelegramConnector

Main table that stores connected bot information:

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique connector identifier |
| `user_id` | UUID | Bot owner user ID |
| `bot_user_name` | String | Bot username (@example_bot) |
| `bot_token` | String | Bot API token |
| `bot_token_secret` | String | Secret token for webhook validation |
| `created_at` | DateTime | Creation date |
| `updated_at` | DateTime | Last update date |

## 🔌 API Endpoints

### 1. Connect Telegram Bot

**`POST /v1/telegram/connect`**

Registers a new Telegram bot and automatically configures its webhook.

**Headers:**
```json
{
  "X-Api-Key": "your_api_key_here",
  "X-User-Id": "user_uuid"
}
```

**Request Body:**
```json
{
  "bot_user_name": "@my_bot",
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
    "bot_user_name": "@my_bot",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

### 2. Webhook for Incoming Messages

**`POST /v1/telegram/webhook/{telegram_connector_id}`**

Endpoint automatically configured by Telegram to receive messages. Telegram sends a complete `Update` object in the request body.

**Headers:**
```json
{
  "Content-Type": "application/json",
  "X-Telegram-Bot-Api-Secret-Token": "generated_secret_token"
}
```

**Request Body (sent by Telegram):**
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
    "text": "Hello from Telegram!"
  }
}
```

**Response:**
```json
{
  "status": "ok"
}
```

### 3. Send Message

**`POST /v1/telegram/send/{telegram_connector_id}`**

Sends a message through the specified bot.

**Headers:**
```json
{
  "X-Api-Key": "your_api_key_here",
  "X-User-Id": "user_uuid"
}
```

**Request Body:**
```json
{
  "chat_id": 123456789,
  "text": "Hello! This is a message from the API"
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

## ⚙️ Environment Variables

### Required Variables

```bash
# General Configuration
ENVIRONMENT=local                              # Runtime environment
HOST=http://localhost:8000                     # API base URL
API_KEY=your_super_secret_api_key             # API key for authentication

# Database
POSTGRESQL_URL=postgresql://user:password@localhost:5432/telegram_connector

# Target Webhook
WEBHOOK_MESSAGE_RECEIVED=https://your-app.com/api/webhook/telegram-message
```

### Optional Variables

```bash
# Logging and Monitoring
SENTRY_DSN=https://your-sentry-dsn.com         # For error tracking
TIME_ZONE=America/Mexico_City                  # Time zone

# Project Configuration
PROJECT__NAME=Telegram Connector
PROJECT__VERSION=1.0.0
PROJECT__DESCRIPTION=API for Telegram integration
```

## 🚀 Installation and Setup

### Prerequisites

- Python 3.12+
- PostgreSQL
- Docker and Docker Compose (optional)

### Installation with Poetry

1. **Clone the repository:**
```bash
git clone https://github.com/ronihdzz/telegram-connector.git
cd telegram-connector
```

2. **Install dependencies:**
```bash
poetry install
```

3. **Configure environment variables:**
```bash
cp .envs/.example.env .envs/.local.env
# Edit .envs/.local.env with your configuration
```

4. **Run the application:**
```bash
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Installation with Docker

1. **Clone and run:**
```bash
git clone https://github.com/ronihdzz/telegram-connector.git
cd telegram-connector
docker-compose up -d
```

## 📖 Usage Examples

### 1. Register a Bot

```python
import requests

# Configuration
API_BASE = "http://localhost:8000/v1"
API_KEY = "your_api_key"
USER_ID = "550e8400-e29b-41d4-a716-446655440001"

# Register bot
response = requests.post(
    f"{API_BASE}/telegram/connect",
    headers={
        "X-Api-Key": API_KEY,
        "X-User-Id": USER_ID
    },
    json={
        "bot_user_name": "@my_test_bot",
        "bot_token": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
    }
)

bot_data = response.json()
connector_id = bot_data["data"]["id"]
print(f"Bot registered with ID: {connector_id}")
```

### 2. Send a Message

```python
# Send message using the registered bot
response = requests.post(
    f"{API_BASE}/telegram/send/{connector_id}",
    headers={
        "X-Api-Key": API_KEY,
        "X-User-Id": USER_ID
    },
    json={
        "chat_id": 123456789,  # Target chat ID
        "text": "Hello from my application!"
    }
)

result = response.json()
print(f"Message sent with ID: {result['data']['telegram_message_id']}")
```

### 3. Configure Target Webhook

To receive incoming messages, set up an endpoint in your application:

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/api/webhook/telegram-message")
async def receive_telegram_message(request: Request):
    """
    Webhook that receives incoming messages from Telegram
    """
    data = await request.json()
    
    print(f"Message received from {data['bot_user_name']}")
    print(f"Chat ID: {data['chat_id']}")
    print(f"Text: {data['text']}")
    print(f"User: {data['user_id']}")
    
    # Process the message here...
    
    return {"status": "processed"}
```

## 📚 Additional Documentation

### API Documentation

Once the application is running, access:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Project Structure

```
telegram-connector/
├── src/
│   ├── api/v1/telegram/          # REST API endpoints
│   ├── db/postgres/models/       # Database models
│   ├── core/settings/            # Application configuration
│   ├── shared/                   # Shared utilities
│   └── tests/                    # Test suites
├── docker_images/                # Docker configurations
├── .envs/                        # Environment variables
└── docs/                         # Additional documentation
```

## 🧪 Testing

Run the test suite:

```bash
# With Poetry
poetry run pytest

# With coverage
poetry run pytest --cov=src --cov-report=html
```

## 🤝 Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


## 👨‍💻 Author

**Ronaldo Hernández** - [@ronihdzz](https://github.com/ronihdzz)

---

<div align="center">

**Like the project? Give it a ⭐!**

[🐛 Report Bug](https://github.com/ronihdzz/telegram-connector/issues) • [✨ Request Feature](https://github.com/ronihdzz/telegram-connector/issues) • [💬 Discussions](https://github.com/ronihdzz/telegram-connector/discussions)

</div>


