import uuid
import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException, Request
from uuid import UUID

from .utils import TelegramDBMixin
from api.v1.telegram.services import ConnectTelegramService, TelegramWebhookService, SendMessageService
from api.v1.telegram.schema import RequestTelegramConnectorCreateSchema, SendMessageIn


# ─────────────────────────  TESTS TELEGRAM SERVICES  ────────────────────────── #

class TestConnectTelegramService(TelegramDBMixin, unittest.TestCase):

    @patch('requests.post')
    def test_connect_success(self, mock_post):
        """Test conexión exitosa con Telegram"""
        # Mock de la respuesta de Telegram API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_post.return_value = mock_response

        # Mock request
        request = MagicMock(spec=Request)
        request.headers = {
            "X-Api-Key": self.test_api_key,
            "X-User-Id": self.test_user_id
        }

        payload = RequestTelegramConnectorCreateSchema(
            bot_user_name="test_bot",
            bot_token="123456:ABC-DEF"
        )

        result = asyncio.run(ConnectTelegramService.connect(payload, request))

        # Verificar respuesta - JSONResponse de FastAPI
        self.assertIsNotNone(result)
        # Como es JSONResponse, necesitamos verificar el status_code y contenido
        self.assertEqual(result.status_code, 200)
        
        # Verificar que se llamó al API de Telegram
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn("setWebhook", args[0])

    def test_connect_missing_api_key(self):
        """Test conexión sin API key"""
        request = MagicMock(spec=Request)
        request.headers = {"X-User-Id": self.test_user_id}

        payload = RequestTelegramConnectorCreateSchema(
            bot_user_name="test_bot",
            bot_token="123456:ABC-DEF"
        )

        with self.assertRaises(HTTPException) as context:
            asyncio.run(ConnectTelegramService.connect(payload, request))
        
        self.assertEqual(context.exception.status_code, 400)

    def test_connect_invalid_api_key(self):
        """Test conexión con API key inválido"""
        request = MagicMock(spec=Request)
        request.headers = {
            "X-Api-Key": "invalid_key",
            "X-User-Id": self.test_user_id
        }

        payload = RequestTelegramConnectorCreateSchema(
            bot_user_name="test_bot",
            bot_token="123456:ABC-DEF"
        )

        with self.assertRaises(HTTPException) as context:
            asyncio.run(ConnectTelegramService.connect(payload, request))
        
        self.assertEqual(context.exception.status_code, 400)

    def test_connect_missing_user_id(self):
        """Test conexión sin User ID"""
        request = MagicMock(spec=Request)
        request.headers = {"X-Api-Key": self.test_api_key}

        payload = RequestTelegramConnectorCreateSchema(
            bot_user_name="test_bot",
            bot_token="123456:ABC-DEF"
        )

        with self.assertRaises(HTTPException) as context:
            asyncio.run(ConnectTelegramService.connect(payload, request))
        
        self.assertEqual(context.exception.status_code, 400)

    @patch('requests.post')
    def test_connect_telegram_api_error(self, mock_post):
        """Test error en API de Telegram"""
        # Mock de error en Telegram API
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        request = MagicMock(spec=Request)
        request.headers = {
            "X-Api-Key": self.test_api_key,
            "X-User-Id": self.test_user_id
        }

        payload = RequestTelegramConnectorCreateSchema(
            bot_user_name="test_bot",
            bot_token="123456:ABC-DEF"
        )

        with self.assertRaises(HTTPException) as context:
            asyncio.run(ConnectTelegramService.connect(payload, request))
        
        self.assertEqual(context.exception.status_code, 500)


class TestTelegramWebhookService(TelegramDBMixin, unittest.TestCase):

    @patch('requests.post')
    def test_webhook_success(self, mock_post):
        """Test procesamiento exitoso de webhook"""
        # Crear conector de prueba
        connector = self.create_test_connector()
        
        # Mock de la respuesta del webhook destino
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Mock request
        request = MagicMock(spec=Request)
        request.json = AsyncMock(return_value=self.telegram_webhook_message())

        result = asyncio.run(TelegramWebhookService.webhook(
            request, 
            str(connector.id), 
            connector.bot_token_secret
        ))

        self.assertEqual(result["status"], "ok")
        mock_post.assert_called_once()

    def test_webhook_invalid_connector(self):
        """Test webhook con ID de conector inválido"""
        fake_id = str(uuid.uuid4())
        
        request = MagicMock(spec=Request)
        request.json = AsyncMock(return_value=self.telegram_webhook_message())

        with self.assertRaises(HTTPException) as context:
            asyncio.run(TelegramWebhookService.webhook(request, fake_id, "any_secret"))
        
        self.assertEqual(context.exception.status_code, 404)

    def test_webhook_invalid_secret(self):
        """Test webhook con secret token inválido"""
        connector = self.create_test_connector()
        
        request = MagicMock(spec=Request)
        request.json = AsyncMock(return_value=self.telegram_webhook_message())

        with self.assertRaises(HTTPException) as context:
            asyncio.run(TelegramWebhookService.webhook(
                request, 
                str(connector.id), 
                "wrong_secret"
            ))
        
        self.assertEqual(context.exception.status_code, 403)

    @patch('requests.post')
    def test_webhook_no_message(self, mock_post):
        """Test webhook sin mensaje (update ignorado)"""
        connector = self.create_test_connector()
        
        request = MagicMock(spec=Request)
        request.json = AsyncMock(return_value={"update_id": 123})

        result = asyncio.run(TelegramWebhookService.webhook(
            request, 
            str(connector.id), 
            connector.bot_token_secret
        ))

        self.assertEqual(result["status"], "ignored")
        mock_post.assert_not_called()

    @patch('requests.post')
    def test_webhook_edited_message(self, mock_post):
        """Test webhook con mensaje editado"""
        connector = self.create_test_connector()
        
        # Mock de la respuesta del webhook destino
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Mensaje editado
        webhook_data = {
            "edited_message": {
                "message_id": 123,
                "date": 1640995200,
                "chat": {"id": 12345, "type": "private"},
                "from": {"id": 67890, "is_bot": False, "first_name": "Test"},
                "text": "Mensaje editado"
            }
        }

        request = MagicMock(spec=Request)
        request.json = AsyncMock(return_value=webhook_data)

        result = asyncio.run(TelegramWebhookService.webhook(
            request, 
            str(connector.id), 
            connector.bot_token_secret
        ))

        self.assertEqual(result["status"], "ok")
        mock_post.assert_called_once()


class TestSendMessageService(TelegramDBMixin, unittest.TestCase):

    @patch('requests.post')
    def test_send_message_success(self, mock_post):
        """Test envío exitoso de mensaje"""
        connector = self.create_test_connector()
        
        # Mock de la respuesta de Telegram API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ok": True,
            "result": {
                "message_id": 456,
                "date": 1640995200,
                "chat": {"id": 12345},
                "text": "Mensaje de prueba"
            }
        }
        mock_post.return_value = mock_response

        # Mock request
        request = MagicMock(spec=Request)
        request.headers = self.headers_for_user()

        payload = SendMessageIn(chat_id=12345, text="Mensaje de prueba")

        result = asyncio.run(SendMessageService.send(connector.id, payload, request))

        # Verificar respuesta - JSONResponse de FastAPI
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 200)
        
        # Verificar que se llamó al API de Telegram
        mock_post.assert_called_once()

    def test_send_message_invalid_connector(self):
        """Test envío con ID de conector inválido"""
        fake_id = uuid.uuid4()
        
        request = MagicMock(spec=Request)
        request.headers = self.headers_for_user()

        payload = SendMessageIn(chat_id=12345, text="Mensaje de prueba")

        with self.assertRaises(HTTPException) as context:
            asyncio.run(SendMessageService.send(fake_id, payload, request))
        
        self.assertEqual(context.exception.status_code, 404)

    def test_send_message_wrong_user(self):
        """Test envío con usuario incorrecto"""
        connector = self.create_test_connector()
        different_user_id = str(uuid.uuid4())
        
        request = MagicMock(spec=Request)
        request.headers = self.headers_for_user(different_user_id)

        payload = SendMessageIn(chat_id=12345, text="Mensaje de prueba")

        with self.assertRaises(HTTPException) as context:
            asyncio.run(SendMessageService.send(connector.id, payload, request))
        
        self.assertEqual(context.exception.status_code, 403)

    def test_send_message_missing_api_key(self):
        """Test envío sin API key"""
        connector = self.create_test_connector()
        
        request = MagicMock(spec=Request)
        request.headers = {"X-User-Id": self.test_user_id}

        payload = SendMessageIn(chat_id=12345, text="Mensaje de prueba")

        with self.assertRaises(HTTPException) as context:
            asyncio.run(SendMessageService.send(connector.id, payload, request))
        
        self.assertEqual(context.exception.status_code, 400)

    def test_send_message_invalid_api_key(self):
        """Test envío con API key inválido"""
        connector = self.create_test_connector()
        
        request = MagicMock(spec=Request)
        request.headers = {
            "X-Api-Key": "invalid_key",
            "X-User-Id": self.test_user_id
        }

        payload = SendMessageIn(chat_id=12345, text="Mensaje de prueba")

        with self.assertRaises(HTTPException) as context:
            asyncio.run(SendMessageService.send(connector.id, payload, request))
        
        self.assertEqual(context.exception.status_code, 400)

    @patch('requests.post')
    def test_send_message_telegram_api_error(self, mock_post):
        """Test error en API de Telegram"""
        connector = self.create_test_connector()
        
        # Mock de error en Telegram API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ok": False,
            "description": "Bad Request: chat not found"
        }
        mock_post.return_value = mock_response

        request = MagicMock(spec=Request)
        request.headers = self.headers_for_user()

        payload = SendMessageIn(chat_id=12345, text="Mensaje de prueba")

        with self.assertRaises(HTTPException) as context:
            asyncio.run(SendMessageService.send(connector.id, payload, request))
        
        self.assertEqual(context.exception.status_code, 502) 