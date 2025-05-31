from loguru import logger

from core.settings import settings
from db.posgresql.models.public import (  # import all models for create tables for database testing
    Book
)
from shared.environment import AppEnvironment
from tests.utils.create_databases import prepare_database

logger.info(f"Check if ENVIRONMENT=testing: {settings.ENVIRONMENT} in {AppEnvironment.TESTING.value} or {AppEnvironment.TESTING_DOCKER.value}")
if settings.ENVIRONMENT in [AppEnvironment.TESTING.value, AppEnvironment.TESTING_DOCKER.value]:
    logger.info("Preparing database for tests")
    prepare_database(
        schemas_to_create=["public"],
    )