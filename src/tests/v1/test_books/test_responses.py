import unittest
from .utils import DBMixin

class TestEnvelopeFormat(DBMixin, unittest.TestCase):
    """Comprueba estructura genérica del sobre de respuesta."""

    def test_envelope_keys(self):
        res = self.client.get("/v1/books")
        env = res.json()
        self.assertSetEqual(
            set(env.keys()), {"success", "message", "data", "trace_id"}
        )
        self.assertIsInstance(env["success"], bool)
        self.assertTrue(env["message"])
        # trace_id puede ser None o str
        self.assertTrue(env["trace_id"] is None or isinstance(env["trace_id"], str))

