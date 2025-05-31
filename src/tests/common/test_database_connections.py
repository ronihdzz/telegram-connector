from unittest import TestCase
from sqlalchemy import create_engine, text
from pymongo import MongoClient
from redis import Redis
import os
from core.settings import settings

class TestDatabaseConnections(TestCase):

    def test_postgresql_connection(self) -> None:
        engine = create_engine(settings.POSTGRESQL_URL.unicode_string())
        self.assertIsNotNone(engine)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1;"))
            self.assertIsNotNone(result)
            self.assertTrue(result.fetchone()[0] == 1) # type: ignore
        engine.dispose()

    def test_mongodb_connection(self) -> None:
        client = MongoClient(settings.MONGO_URL.unicode_string()) # type: ignore
        server_info = client.server_info()
        self.assertIn("version", server_info)
        client.close()

    def test_redis_connection(self) -> None:
        redis = Redis.from_url(settings.REDIS_URL.unicode_string())
        self.assertTrue(redis.ping())
        redis.close()