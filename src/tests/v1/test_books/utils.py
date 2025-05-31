from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text

from main import app                                     
from db.posgresql import get_db_context                  
from db.posgresql.models.public import BookType
from api.v1.books.schema import BookCreateSchema

class DBMixin:
    """Métodos auxiliares para limpiar la tabla `book` entre tests."""

    @staticmethod
    def _truncate_books() -> None:
        with get_db_context() as session:
            session.execute(
                text("TRUNCATE TABLE public.books RESTART IDENTITY CASCADE;")
            )
            session.commit()

    def setUp(self) -> None:     # se ejecuta antes de *cada* test
        self._truncate_books()
        self.client = TestClient(app)

    def tearDown(self) -> None:  # limpieza final
        self._truncate_books()

    # ---------- datos de apoyo ---------- #
    @staticmethod
    def payload(**overrides: Any) -> dict[str, Any]:
        data = {
            "title": "Clean Code",
            "author": "Robert C. Martin",
            "year": 2008,
            "type": BookType.ONLINE.value,  # Enum → string para JSON
        }
        data.update(overrides)
        return data

    @staticmethod
    def create_schema(**overrides: Any) -> BookCreateSchema:
        base = dict(
            title="Domain-Driven Design",
            author="Eric Evans",
            year=2003,
            type=BookType.ONLINE,
        )
        base.update(overrides)
        return BookCreateSchema(**base)
