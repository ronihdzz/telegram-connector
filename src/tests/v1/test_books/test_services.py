import json
import uuid
import unittest
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text

from main import app                                     
from db.posgresql import get_db_context                  
from db.posgresql.models.public import BookType
from api.v1.books.schema import BookCreateSchema
from api.v1.books.repositories import BookRepository
from api.v1.books.services import (
    BooksListService,
    BookCreateService,
    BookRetrieveService,
    BookUpdateService,
    BookDeleteService,
)
from .utils import DBMixin

# ─────────────────────────  TESTS SERVICIOS  ────────────────────────── #

class TestBooksServices(DBMixin, unittest.TestCase):

    def test_service_create_retrieve_update_delete_flow(self):
        # CREATE
        schema = self.create_schema()
        created = BookCreateService.create(schema)
        self.assertEqual(created.title, schema.title)

        # LIST debe contener el nuevo
        ids = [b.id for b in BooksListService.list()]
        self.assertIn(created.id, ids)

        # RETRIEVE
        fetched = BookRetrieveService.retrieve(created.id)
        self.assertEqual(fetched.author, schema.author)

        # UPDATE
        upd_schema = self.create_schema(title="DDD Updated", year=2004)
        updated = BookUpdateService.update(created.id, upd_schema)
        self.assertEqual(updated.title, "DDD Updated")
        self.assertEqual(updated.year, 2004)

        # DELETE
        BookDeleteService.delete(created.id)
        with self.assertRaises(Exception):
            BookRetrieveService.retrieve(created.id)

