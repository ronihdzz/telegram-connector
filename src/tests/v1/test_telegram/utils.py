from typing import Any
from uuid import UUID, uuid4
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy import text

from main import app
from db.posgresql import get_db_context
from db.posgresql.models.public import TelegramConnector
from api.v1.telegram.schema import (
    RequestTelegramConnectorCreateSchema,
    TelegramConnectorCreateSchema,
    SendMessageIn,
    WebhookMessageReceived
)
from core.settings import settings


class TelegramDBMixin:
    """Métodos auxiliares para limpiar la tabla `telegram_connectors` entre tests."""

    @staticmethod
    def _truncate_telegram_connectors() -> None:
        with get_db_context() as session:
            session.execute(
                text("TRUNCATE TABLE public.telegram_connectors RESTART IDENTITY CASCADE;")
            )
            session.commit()

    def setUp(self) -> None:     # se ejecuta antes de *cada* test
        self._truncate_telegram_connectors()
        self.client = TestClient(app)
        self.test_user_id = str(uuid4())
        self.test_api_key = settings.API_KEY

    def tearDown(self) -> None:  # limpieza final
        self._truncate_telegram_connectors()

    # ---------- datos de apoyo ---------- #
    @staticmethod
    def connector_payload(**overrides: Any) -> dict[str, Any]:
        data = {
            "bot_user_name": "test_bot",
            "bot_token": "1234567890:TEST_BOT_TOKEN_FOR_TESTING"
        }
        data.update(overrides)
        return data

    @staticmethod
    def send_message_payload(**overrides: Any) -> dict[str, Any]:
        data = {
            "chat_id": 12345,
            "text": "Mensaje de prueba"
        }
        data.update(overrides)
        return data

    def headers_for_user(self, user_id: str = None) -> dict[str, str]:
        return {
            "X-Api-Key": self.test_api_key,
            "X-User-Id": user_id or self.test_user_id
        }

    def webhook_headers(self, secret_token: str) -> dict[str, str]:
        return {
            "X-Telegram-Bot-Api-Secret-Token": secret_token
        }

    @staticmethod
    def telegram_webhook_message(**overrides: Any) -> dict[str, Any]:
        data = {
            "message": {
                "message_id": 123,
                "date": 1640995200,  # timestamp
                "chat": {
                    "id": 12345,
                    "type": "private"
                },
                "from": {
                    "id": 67890,
                    "is_bot": False,
                    "first_name": "Test",
                    "username": "testuser"
                },
                "text": "Hola desde el webhook"
            }
        }
        data.update(overrides)
        return data

    def create_test_connector(self, user_id: str = None) -> TelegramConnector:
        """Crea un conector de prueba en la base de datos"""
        user_id = user_id or self.test_user_id
        schema = TelegramConnectorCreateSchema(
            user_id=UUID(user_id),
            bot_user_name="test_bot",
            bot_token="1234567890:TEST_BOT_TOKEN",
            bot_token_secret="test_secret_token_123"
        )
        
        with get_db_context() as session:
            connector = TelegramConnector(**schema.model_dump())
            session.add(connector)
            session.commit()
            session.refresh(connector)
            return connector 