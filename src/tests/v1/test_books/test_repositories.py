import unittest
from api.v1.books.repositories import BookRepository
from .utils import DBMixin

# ─────────────────────────  TESTS REPOSITORIO  ────────────────────────── #

class TestBooksRepository(DBMixin, unittest.TestCase):

    def test_repository_crud(self):
        # CREATE
        ok, book = BookRepository.create(self.create_schema())
        self.assertTrue(ok)
        self.assertIsNotNone(book.id)

        # GET ALL
        ok, all_books = BookRepository.get_all()
        self.assertTrue(ok)
        self.assertEqual(len(all_books), 1)

        # GET BY ID
        ok, fetched = BookRepository.get_by_id(book.id)
        self.assertTrue(ok)
        self.assertEqual(fetched.title, book.title)

        # UPDATE
        new_schema = self.create_schema(title="Pragmatic Programmer", year=1999)
        ok, updated = BookRepository.update(book.id, new_schema)
        self.assertTrue(ok)
        self.assertEqual(updated.title, "Pragmatic Programmer")

        # DELETE
        ok, _ = BookRepository.delete(book.id)
        self.assertTrue(ok)

        # Ya no existe
        ok, none = BookRepository.get_by_id(book.id)
        self.assertFalse(ok)
        self.assertIsNone(none)
