from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

from db.posgresql import Base
from core.settings import settings


def create_schema(engine, schema_name):
    schema_format = "CREATE SCHEMA IF NOT EXISTS {}"
    query_schema = text(schema_format.format(schema_name))
    with engine.connect() as conn, conn.begin():
        conn.execute(query_schema)


def create_schemas(engine, schemas_to_create: list[str]):
    for schema in schemas_to_create:
        create_schema(engine, schema)


def prepare_database(schemas_to_create: list[str]):
    engine = create_engine(settings.POSTGRESQL_URL.unicode_string(), poolclass=NullPool)
    create_schemas(engine, schemas_to_create)
    Base.metadata.create_all(engine)