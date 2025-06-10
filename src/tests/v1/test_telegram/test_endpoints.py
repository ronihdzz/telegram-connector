import uuid
import unittest
from unittest.mock import patch, MagicMock
from .utils import TelegramDBMixin


# ─────────────────────────  TESTS TELEGRAM ENDPOINTS  ────────────────────────── #

class TestTelegramEndpoints(TelegramDBMixin, unittest.TestCase):

    # ---------- POST /telegram/connect ---------- #
    @patch('requests.post')
    def test_connect_telegram_success(self, mock_post):
        # Mock de la respuesta de Telegram API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_post.return_value = mock_response

        payload = self.connector_payload()
        headers = self.headers_for_user()
        
        res = self.client.post("/v1/telegram/connect", json=payload, headers=headers)
        
        self.assertEqual(res.status_code, 200)
        env = res.json()
        self.assertTrue(env["success"])
        
        data = env["data"]
        # Verificar que se devuelve un ID válido
        uuid.UUID(data["id"])
        self.assertEqual(data["bot_user_name"], "test_bot")
        self.assertEqual(data["user_id"], self.test_user_id)
        
        # Verificar que se llamó al API de Telegram
        mock_post.assert_called_once()

    def test_connect_telegram_missing_api_key(self):
        payload = self.connector_payload()
        headers = {"X-User-Id": self.test_user_id}  # Sin API Key
        
        res = self.client.post("/v1/telegram/connect", json=payload, headers=headers)
        
        self.assertEqual(res.status_code, 400)

    def test_connect_telegram_invalid_api_key(self):
        payload = self.connector_payload()
        headers = {
            "X-Api-Key": "invalid_key",
            "X-User-Id": self.test_user_id
        }
        
        res = self.client.post("/v1/telegram/connect", json=payload, headers=headers)
        
        self.assertEqual(res.status_code, 400)

    def test_connect_telegram_missing_user_id(self):
        payload = self.connector_payload()
        headers = {"X-Api-Key": self.test_api_key}  # Sin User ID
        
        res = self.client.post("/v1/telegram/connect", json=payload, headers=headers)
        
        self.assertEqual(res.status_code, 400)

    @patch('requests.post')
    def test_connect_telegram_api_error(self, mock_post):
        # Mock de error en Telegram API
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        payload = self.connector_payload()
        headers = self.headers_for_user()
        
        res = self.client.post("/v1/telegram/connect", json=payload, headers=headers)
        
        self.assertEqual(res.status_code, 500)

    def test_connect_telegram_missing_fields(self):
        payload = {"bot_user_name": "test_bot"}  # Sin bot_token
        headers = self.headers_for_user()
        
        res = self.client.post("/v1/telegram/connect", json=payload, headers=headers)
        
        self.assertEqual(res.status_code, 400)

    # ---------- POST /telegram/webhook/{telegram_connector_id} ---------- #
    @patch('requests.post')
    def test_webhook_success(self, mock_post):
        # Crear conector de prueba
        connector = self.create_test_connector()
        
        # Mock de la respuesta del webhook destino
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        webhook_payload = self.telegram_webhook_message()
        headers = self.webhook_headers(connector.bot_token_secret)
        
        res = self.client.post(
            f"/v1/telegram/webhook/{connector.id}", 
            json=webhook_payload, 
            headers=headers
        )
        
        self.assertEqual(res.status_code, 200)
        response_data = res.json()
        self.assertEqual(response_data["status"], "ok")
        
        # Verificar que se llamó al webhook destino
        mock_post.assert_called_once()

    def test_webhook_invalid_connector_id(self):
        fake_id = str(uuid.uuid4())
        webhook_payload = self.telegram_webhook_message()
        headers = self.webhook_headers("any_secret")
        
        res = self.client.post(
            f"/v1/telegram/webhook/{fake_id}", 
            json=webhook_payload, 
            headers=headers
        )
        
        self.assertEqual(res.status_code, 404)

    def test_webhook_invalid_secret_token(self):
        connector = self.create_test_connector()
        webhook_payload = self.telegram_webhook_message()
        headers = self.webhook_headers("wrong_secret")
        
        res = self.client.post(
            f"/v1/telegram/webhook/{connector.id}", 
            json=webhook_payload, 
            headers=headers
        )
        
        self.assertEqual(res.status_code, 403)

    def test_webhook_missing_secret_token(self):
        connector = self.create_test_connector()
        webhook_payload = self.telegram_webhook_message()
        
        res = self.client.post(
            f"/v1/telegram/webhook/{connector.id}", 
            json=webhook_payload
        )
        
        self.assertEqual(res.status_code, 403)

    @patch('requests.post')
    def test_webhook_no_message(self, mock_post):
        connector = self.create_test_connector()
        webhook_payload = {"update_id": 123}  # Sin mensaje
        headers = self.webhook_headers(connector.bot_token_secret)
        
        res = self.client.post(
            f"/v1/telegram/webhook/{connector.id}", 
            json=webhook_payload, 
            headers=headers
        )
        
        self.assertEqual(res.status_code, 200)
        response_data = res.json()
        self.assertEqual(response_data["status"], "ignored")
        
        # No debería llamar al webhook destino
        mock_post.assert_not_called()

    @patch('requests.post')
    def test_webhook_edited_message(self, mock_post):
        connector = self.create_test_connector()
        
        # Mock de la respuesta del webhook destino
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Mensaje editado
        webhook_payload = {
            "edited_message": {
                "message_id": 123,
                "date": 1640995200,
                "chat": {"id": 12345, "type": "private"},
                "from": {"id": 67890, "is_bot": False, "first_name": "Test"},
                "text": "Mensaje editado"
            }
        }
        headers = self.webhook_headers(connector.bot_token_secret)
        
        res = self.client.post(
            f"/v1/telegram/webhook/{connector.id}", 
            json=webhook_payload, 
            headers=headers
        )
        
        self.assertEqual(res.status_code, 200)
        response_data = res.json()
        self.assertEqual(response_data["status"], "ok")

    # ---------- POST /telegram/send/{telegram_connector_id} ---------- #
    @patch('requests.post')
    def test_send_message_success(self, mock_post):
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

        payload = self.send_message_payload()
        headers = self.headers_for_user()
        
        res = self.client.post(
            f"/v1/telegram/send/{connector.id}", 
            json=payload, 
            headers=headers
        )
        
        self.assertEqual(res.status_code, 200)
        env = res.json()
        self.assertTrue(env["success"])
        
        data = env["data"]
        self.assertEqual(data["telegram_message_id"], 456)
        self.assertEqual(data["status"], "sent")

    def test_send_message_invalid_connector_id(self):
        fake_id = str(uuid.uuid4())
        payload = self.send_message_payload()
        headers = self.headers_for_user()
        
        res = self.client.post(
            f"/v1/telegram/send/{fake_id}", 
            json=payload, 
            headers=headers
        )
        
        self.assertEqual(res.status_code, 404)

    def test_send_message_wrong_user(self):
        connector = self.create_test_connector()
        different_user_id = str(uuid.uuid4())
        
        payload = self.send_message_payload()
        headers = self.headers_for_user(different_user_id)
        
        res = self.client.post(
            f"/v1/telegram/send/{connector.id}", 
            json=payload, 
            headers=headers
        )
        
        self.assertEqual(res.status_code, 403)

    def test_send_message_missing_api_key(self):
        connector = self.create_test_connector()
        payload = self.send_message_payload()
        headers = {"X-User-Id": self.test_user_id}  # Sin API Key
        
        res = self.client.post(
            f"/v1/telegram/send/{connector.id}", 
            json=payload, 
            headers=headers
        )
        
        self.assertEqual(res.status_code, 400)

    def test_send_message_invalid_api_key(self):
        connector = self.create_test_connector()
        payload = self.send_message_payload()
        headers = {
            "X-Api-Key": "invalid_key",
            "X-User-Id": self.test_user_id
        }
        
        res = self.client.post(
            f"/v1/telegram/send/{connector.id}", 
            json=payload, 
            headers=headers
        )
        
        self.assertEqual(res.status_code, 400)

    @patch('requests.post')
    def test_send_message_telegram_api_error(self, mock_post):
        connector = self.create_test_connector()
        
        # Mock de error en Telegram API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ok": False,
            "description": "Bad Request: chat not found"
        }
        mock_post.return_value = mock_response

        payload = self.send_message_payload()
        headers = self.headers_for_user()
        
        res = self.client.post(
            f"/v1/telegram/send/{connector.id}", 
            json=payload, 
            headers=headers
        )
        
        self.assertEqual(res.status_code, 502)

    def test_send_message_invalid_payload(self):
        connector = self.create_test_connector()
        payload = {"chat_id": "invalid"}  # chat_id debe ser int
        headers = self.headers_for_user()
        
        res = self.client.post(
            f"/v1/telegram/send/{connector.id}", 
            json=payload, 
            headers=headers
        )
        
        self.assertEqual(res.status_code, 400)

    def test_send_message_empty_text(self):
        connector = self.create_test_connector()
        payload = {
            "chat_id": 12345,
            "text": ""  # Texto vacío
        }
        headers = self.headers_for_user()
        
        res = self.client.post(
            f"/v1/telegram/send/{connector.id}", 
            json=payload, 
            headers=headers
        )
        
        self.assertEqual(res.status_code, 400)

    def test_send_message_text_too_long(self):
        connector = self.create_test_connector()
        payload = {
            "chat_id": 12345,
            "text": "x" * 5000  # Más de 4096 caracteres
        }
        headers = self.headers_for_user()
        
        res = self.client.post(
            f"/v1/telegram/send/{connector.id}", 
            json=payload, 
            headers=headers
        )
        
        self.assertEqual(res.status_code, 400) 