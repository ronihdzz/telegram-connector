import unittest
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import ValidationError

from api.v1.telegram.schema import (
    RequestTelegramConnectorCreateSchema,
    TelegramConnectorCreateSchema,
    TelegramConnectorCreateResponseSchema,
    SendMessageIn,
    SendMessageOut,
    WebhookMessageReceived
)


# ─────────────────────────  TESTS TELEGRAM SCHEMAS  ────────────────────────── #

class TestRequestTelegramConnectorCreateSchema(unittest.TestCase):

    def test_valid_schema(self):
        """Test schema válido"""
        data = {
            "bot_user_name": "test_bot",
            "bot_token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        }
        
        schema = RequestTelegramConnectorCreateSchema(**data)
        
        self.assertEqual(schema.bot_user_name, "test_bot")
        self.assertEqual(schema.bot_token, "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")

    def test_missing_bot_user_name(self):
        """Test sin bot_user_name"""
        data = {
            "bot_token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        }
        
        with self.assertRaises(ValidationError):
            RequestTelegramConnectorCreateSchema(**data)

    def test_missing_bot_token(self):
        """Test sin bot_token"""
        data = {
            "bot_user_name": "test_bot"
        }
        
        with self.assertRaises(ValidationError):
            RequestTelegramConnectorCreateSchema(**data)

    def test_empty_bot_user_name(self):
        """Test con bot_user_name vacío"""
        data = {
            "bot_user_name": "",
            "bot_token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        }
        
        schema = RequestTelegramConnectorCreateSchema(**data)
        self.assertEqual(schema.bot_user_name, "")

    def test_empty_bot_token(self):
        """Test con bot_token vacío"""
        data = {
            "bot_user_name": "test_bot",
            "bot_token": ""
        }
        
        schema = RequestTelegramConnectorCreateSchema(**data)
        self.assertEqual(schema.bot_token, "")


class TestTelegramConnectorCreateSchema(unittest.TestCase):

    def test_valid_schema(self):
        """Test schema válido"""
        user_id = uuid4()
        data = {
            "user_id": user_id,
            "bot_user_name": "test_bot",
            "bot_token": "123456:ABC-DEF",
            "bot_token_secret": "secret123"
        }
        
        schema = TelegramConnectorCreateSchema(**data)
        
        self.assertEqual(schema.user_id, user_id)
        self.assertEqual(schema.bot_user_name, "test_bot")
        self.assertEqual(schema.bot_token, "123456:ABC-DEF")
        self.assertEqual(schema.bot_token_secret, "secret123")

    def test_missing_user_id(self):
        """Test sin user_id"""
        data = {
            "bot_user_name": "test_bot",
            "bot_token": "123456:ABC-DEF",
            "bot_token_secret": "secret123"
        }
        
        with self.assertRaises(ValidationError):
            TelegramConnectorCreateSchema(**data)

    def test_invalid_user_id(self):
        """Test con user_id inválido"""
        data = {
            "user_id": "invalid-uuid",
            "bot_user_name": "test_bot",
            "bot_token": "123456:ABC-DEF",
            "bot_token_secret": "secret123"
        }
        
        with self.assertRaises(ValidationError):
            TelegramConnectorCreateSchema(**data)


class TestTelegramConnectorCreateResponseSchema(unittest.TestCase):

    def test_valid_schema(self):
        """Test schema válido"""
        user_id = uuid4()
        connector_id = uuid4()
        now = datetime.now()
        
        data = {
            "id": connector_id,
            "user_id": user_id,
            "bot_user_name": "test_bot",
            "created_at": now,
            "updated_at": now
        }
        
        schema = TelegramConnectorCreateResponseSchema(**data)
        
        self.assertEqual(schema.id, connector_id)
        self.assertEqual(schema.user_id, user_id)
        self.assertEqual(schema.bot_user_name, "test_bot")
        self.assertEqual(schema.created_at, now)
        self.assertEqual(schema.updated_at, now)

    def test_serialization(self):
        """Test serialización de UUIDs y fechas"""
        user_id = uuid4()
        connector_id = uuid4()
        now = datetime.now()
        
        data = {
            "id": connector_id,
            "user_id": user_id,
            "bot_user_name": "test_bot",
            "created_at": now,
            "updated_at": now
        }
        
        schema = TelegramConnectorCreateResponseSchema(**data)
        json_data = schema.model_dump(mode="json")
        
        # Verificar que los UUIDs se serializan como strings
        self.assertEqual(json_data["id"], str(connector_id))
        self.assertEqual(json_data["user_id"], str(user_id))
        
        # Verificar que las fechas se serializan como ISO strings
        self.assertEqual(json_data["created_at"], now.isoformat())
        self.assertEqual(json_data["updated_at"], now.isoformat())


class TestSendMessageIn(unittest.TestCase):

    def test_valid_schema(self):
        """Test schema válido"""
        data = {
            "chat_id": 12345,
            "text": "Mensaje de prueba"
        }
        
        schema = SendMessageIn(**data)
        
        self.assertEqual(schema.chat_id, 12345)
        self.assertEqual(schema.text, "Mensaje de prueba")

    def test_missing_chat_id(self):
        """Test sin chat_id"""
        data = {
            "text": "Mensaje de prueba"
        }
        
        with self.assertRaises(ValidationError):
            SendMessageIn(**data)

    def test_missing_text(self):
        """Test sin text"""
        data = {
            "chat_id": 12345
        }
        
        with self.assertRaises(ValidationError):
            SendMessageIn(**data)

    def test_invalid_chat_id(self):
        """Test con chat_id inválido"""
        data = {
            "chat_id": "invalid",
            "text": "Mensaje de prueba"
        }
        
        with self.assertRaises(ValidationError):
            SendMessageIn(**data)

    def test_empty_text(self):
        """Test con texto vacío"""
        data = {
            "chat_id": 12345,
            "text": ""
        }
        
        with self.assertRaises(ValidationError):
            SendMessageIn(**data)

    def test_text_too_long(self):
        """Test con texto demasiado largo"""
        data = {
            "chat_id": 12345,
            "text": "x" * 5000  # Más de 4096 caracteres
        }
        
        with self.assertRaises(ValidationError):
            SendMessageIn(**data)

    def test_text_max_length(self):
        """Test con texto de longitud máxima"""
        data = {
            "chat_id": 12345,
            "text": "x" * 4096  # Exactamente 4096 caracteres
        }
        
        schema = SendMessageIn(**data)
        self.assertEqual(len(schema.text), 4096)

    def test_negative_chat_id(self):
        """Test con chat_id negativo (válido para grupos)"""
        data = {
            "chat_id": -12345,
            "text": "Mensaje de prueba"
        }
        
        schema = SendMessageIn(**data)
        self.assertEqual(schema.chat_id, -12345)


class TestSendMessageOut(unittest.TestCase):

    def test_valid_schema(self):
        """Test schema válido"""
        data = {
            "telegram_message_id": 456,
            "status": "sent"
        }
        
        schema = SendMessageOut(**data)
        
        self.assertEqual(schema.telegram_message_id, 456)
        self.assertEqual(schema.status, "sent")

    def test_default_status(self):
        """Test valor por defecto de status"""
        data = {
            "telegram_message_id": 456
        }
        
        schema = SendMessageOut(**data)
        
        self.assertEqual(schema.telegram_message_id, 456)
        self.assertEqual(schema.status, "sent")

    def test_missing_telegram_message_id(self):
        """Test sin telegram_message_id"""
        data = {
            "status": "sent"
        }
        
        with self.assertRaises(ValidationError):
            SendMessageOut(**data)

    def test_invalid_telegram_message_id(self):
        """Test con telegram_message_id inválido"""
        data = {
            "telegram_message_id": "invalid",
            "status": "sent"
        }
        
        with self.assertRaises(ValidationError):
            SendMessageOut(**data)


class TestWebhookMessageReceived(unittest.TestCase):

    def test_valid_schema(self):
        """Test schema válido"""
        user_id = uuid4()
        connector_id = uuid4()
        now = datetime.now()
        
        data = {
            "date": now,
            "message_id": 123,
            "chat_id": 12345,
            "text": "Mensaje recibido",
            "user_id": user_id,
            "bot_user_name": "test_bot",
            "connector_id": connector_id
        }
        
        schema = WebhookMessageReceived(**data)
        
        self.assertEqual(schema.date, now)
        self.assertEqual(schema.message_id, 123)
        self.assertEqual(schema.chat_id, 12345)
        self.assertEqual(schema.text, "Mensaje recibido")
        self.assertEqual(schema.user_id, user_id)
        self.assertEqual(schema.bot_user_name, "test_bot")
        self.assertEqual(schema.connector_id, connector_id)

    def test_optional_fields(self):
        """Test campos opcionales"""
        user_id = uuid4()
        connector_id = uuid4()
        now = datetime.now()
        
        data = {
            "date": now,
            "message_id": 123,
            "chat_id": 12345,
            "caption": "Pie de foto",
            "photo": ["photo1.jpg", "photo2.jpg"],
            "sticker": "sticker_id",
            "user_id": user_id,
            "bot_user_name": "test_bot",
            "connector_id": connector_id
        }
        
        schema = WebhookMessageReceived(**data)
        
        self.assertIsNone(schema.text)
        self.assertEqual(schema.caption, "Pie de foto")
        self.assertEqual(schema.photo, ["photo1.jpg", "photo2.jpg"])
        self.assertEqual(schema.sticker, "sticker_id")

    def test_serialization(self):
        """Test serialización de UUIDs"""
        user_id = uuid4()
        connector_id = uuid4()
        now = datetime.now()
        
        data = {
            "date": now,
            "message_id": 123,
            "chat_id": 12345,
            "text": "Mensaje recibido",
            "user_id": user_id,
            "bot_user_name": "test_bot",
            "connector_id": connector_id
        }
        
        schema = WebhookMessageReceived(**data)
        json_data = schema.model_dump(mode="json")
        
        # Verificar que los UUIDs se serializan como strings
        self.assertEqual(json_data["user_id"], str(user_id))
        self.assertEqual(json_data["connector_id"], str(connector_id))

    def test_missing_required_fields(self):
        """Test campos requeridos faltantes"""
        data = {
            "date": datetime.now(),
            "message_id": 123,
            "chat_id": 12345
            # Faltan user_id, bot_user_name, connector_id
        }
        
        with self.assertRaises(ValidationError):
            WebhookMessageReceived(**data) 