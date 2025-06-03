from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from core.settings import settings
from db.posgresql.base import Base
from db.posgresql.models.public import TelegramConnector 
from loguru import logger

def create_specific_tables(engine, tables: list):
    for table in tables:
        logger.info(f"Creating table: {table.name}")
        table.create(engine, checkfirst=True)  # checkfirst=True solo crea si no existe


def prepare_specific_tables(models: list):
    logger.info(f"Creating tables")
    engine = create_engine(
        settings.POSTGRESQL_URL.unicode_string(),
        poolclass=NullPool,
        echo=True  # <-- ¡Activa logs!
    )
    logger.info(f"Engine created")
    tables = [model.__table__ for model in models]
    create_specific_tables(engine, tables)
    logger.info(f"Tables created")

if __name__ == "__main__":
    logger.info(f"Creating tables")
    prepare_specific_tables(
        models=[
            TelegramConnector
        ]
    )
