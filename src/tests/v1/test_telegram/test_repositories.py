import uuid
import unittest
from uuid import UUID

from .utils import TelegramDBMixin
from api.v1.telegram.repositories import TelegramConnectorRepository
from api.v1.telegram.schema import TelegramConnectorCreateSchema


# ─────────────────────────  TESTS TELEGRAM REPOSITORIES  ────────────────────────── #

class TestTelegramConnectorRepository(TelegramDBMixin, unittest.TestCase):

    def test_create_connector_success(self):
        """Test crear un conector de telegram correctamente"""
        user_id = UUID(self.test_user_id)
        schema = TelegramConnectorCreateSchema(
            user_id=user_id,
            bot_user_name="test_bot",
            bot_token="123456:ABC-DEF",
            bot_token_secret="secret_token_123"
        )
        
        success, connector = TelegramConnectorRepository.create(schema)
        
        self.assertTrue(success)
        self.assertIsNotNone(connector)
        self.assertEqual(connector.user_id, user_id)
        self.assertEqual(connector.bot_user_name, "test_bot")
        self.assertEqual(connector.bot_token, "123456:ABC-DEF")
        self.assertEqual(connector.bot_token_secret, "secret_token_123")
        self.assertIsNotNone(connector.id)
        self.assertIsNotNone(connector.created_at)
        self.assertIsNotNone(connector.updated_at)

    def test_get_by_id_existing(self):
        """Test obtener conector por ID existente"""
        # Crear un conector primero
        connector = self.create_test_connector()
        
        success, found_connector = TelegramConnectorRepository.get_by_id(connector.id)
        
        self.assertTrue(success)
        self.assertIsNotNone(found_connector)
        self.assertEqual(found_connector.id, connector.id)
        self.assertEqual(found_connector.user_id, connector.user_id)
        self.assertEqual(found_connector.bot_user_name, connector.bot_user_name)

    def test_get_by_id_nonexistent(self):
        """Test obtener conector por ID que no existe"""
        fake_id = uuid.uuid4()
        
        success, connector = TelegramConnectorRepository.get_by_id(fake_id)
        
        self.assertTrue(success)  # El método siempre devuelve True
        self.assertIsNone(connector)

    def test_get_by_user_id_existing(self):
        """Test obtener conectores por user_id existente"""
        user_id = UUID(self.test_user_id)
        
        # Crear varios conectores para el mismo usuario
        connector1 = self.create_test_connector()
        connector2 = self.create_test_connector()
        
        success, connectors = TelegramConnectorRepository.get_by_user_id(user_id)
        
        self.assertTrue(success)
        self.assertEqual(len(connectors), 2)
        
        # Verificar que ambos conectores pertenecen al usuario correcto
        for connector in connectors:
            self.assertEqual(connector.user_id, user_id)

    def test_get_by_user_id_empty(self):
        """Test obtener conectores por user_id que no tiene conectores"""
        fake_user_id = uuid.uuid4()
        
        success, connectors = TelegramConnectorRepository.get_by_user_id(fake_user_id)
        
        self.assertTrue(success)
        self.assertEqual(len(connectors), 0)

    def test_get_by_user_id_different_users(self):
        """Test que get_by_user_id solo devuelve conectores del usuario solicitado"""
        user1_id = UUID(self.test_user_id)
        user2_id = uuid.uuid4()
        
        # Crear conector para user1
        connector1 = self.create_test_connector(str(user1_id))
        
        # Crear conector para user2
        connector2 = self.create_test_connector(str(user2_id))
        
        # Obtener conectores para user1
        success, connectors_user1 = TelegramConnectorRepository.get_by_user_id(user1_id)
        
        self.assertTrue(success)
        self.assertEqual(len(connectors_user1), 1)
        self.assertEqual(connectors_user1[0].user_id, user1_id)
        
        # Obtener conectores para user2
        success, connectors_user2 = TelegramConnectorRepository.get_by_user_id(user2_id)
        
        self.assertTrue(success)
        self.assertEqual(len(connectors_user2), 1)
        self.assertEqual(connectors_user2[0].user_id, user2_id)

    def test_get_all_empty(self):
        """Test obtener todos los conectores cuando no hay ninguno"""
        success, connectors = TelegramConnectorRepository.get_all()
        
        self.assertTrue(success)
        self.assertEqual(len(connectors), 0)

    def test_get_all_with_connectors(self):
        """Test obtener todos los conectores cuando hay varios"""
        # Crear varios conectores
        connector1 = self.create_test_connector()
        connector2 = self.create_test_connector(str(uuid.uuid4()))
        
        success, connectors = TelegramConnectorRepository.get_all()
        
        self.assertTrue(success)
        self.assertEqual(len(connectors), 2)
        
        # Verificar que los IDs están en la lista
        connector_ids = [c.id for c in connectors]
        self.assertIn(connector1.id, connector_ids)
        self.assertIn(connector2.id, connector_ids)

    def test_delete_existing_connector(self):
        """Test eliminar un conector existente"""
        connector = self.create_test_connector()
        bot_user_name = connector.bot_user_name
        
        success, result = TelegramConnectorRepository.delete(bot_user_name)
        
        self.assertTrue(success)
        self.assertIsNone(result)
        
        # Verificar que ya no existe
        success, found_connector = TelegramConnectorRepository.get_by_id(connector.id)
        self.assertTrue(success)
        self.assertIsNone(found_connector)

    def test_delete_nonexistent_connector(self):
        """Test eliminar un conector que no existe"""
        success, result = TelegramConnectorRepository.delete("nonexistent_bot")
        
        self.assertFalse(success)
        self.assertIsNone(result)

    def test_delete_only_target_connector(self):
        """Test que delete solo elimina el conector específico"""
        # Crear dos conectores
        connector1 = self.create_test_connector()
        connector2_schema = TelegramConnectorCreateSchema(
            user_id=UUID(str(uuid.uuid4())),
            bot_user_name="different_bot",
            bot_token="different_token",
            bot_token_secret="different_secret"
        )
        success, connector2 = TelegramConnectorRepository.create(connector2_schema)
        self.assertTrue(success)
        
        # Eliminar solo el primero
        success, result = TelegramConnectorRepository.delete(connector1.bot_user_name)
        self.assertTrue(success)
        
        # Verificar que el primero ya no existe
        success, found_connector1 = TelegramConnectorRepository.get_by_id(connector1.id)
        self.assertTrue(success)
        self.assertIsNone(found_connector1)
        
        # Verificar que el segundo sigue existiendo
        success, found_connector2 = TelegramConnectorRepository.get_by_id(connector2.id)
        self.assertTrue(success)
        self.assertIsNotNone(found_connector2)
        self.assertEqual(found_connector2.id, connector2.id) 