import uuid
import unittest
from .utils import DBMixin


# ─────────────────────────  TESTS ENDPOINTS  ────────────────────────── #

class TestBooksEndpoints(DBMixin, unittest.TestCase):

    # ---------- GET /books vacío ---------- #
    def test_list_books_empty(self):
        res = self.client.get("/v1/books")
        self.assertEqual(res.status_code, 200)
        env = res.json()
        self.assertTrue(env["success"])
        self.assertIsNone(env["data"])

    # ---------- POST /books ---------- #
    def test_create_book_success(self):
        res = self.client.post("/v1/books", json=self.payload())
        self.assertEqual(res.status_code, 201)
        env = res.json()
        book = env["data"]
        # id válido
        uuid.UUID(book["id"])
        self.assertEqual(book["title"], "Clean Code")

    def test_create_book_missing_field(self):
        bad = self.payload()
        bad.pop("title")
        res = self.client.post("/v1/books", json=bad)
        self.assertEqual(res.status_code, 422)  # validation error

    # ---------- GET /books/{id} ---------- #
    def test_get_book_success(self):
        book_id = self.client.post("/v1/books", json=self.payload()) \
                             .json()["data"]["id"]

        res = self.client.get(f"/v1/books/{book_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["data"]["id"], book_id)

    def test_get_book_not_found(self):
        fake = "11111111-1111-1111-1111-111111111111"
        res = self.client.get(f"/v1/books/{fake}")
        self.assertEqual(res.status_code, 404)
        env = res.json()
        self.assertFalse(env["success"])
        self.assertEqual(
            env["data"]["internal_error"]["code"], "BOOK_NOT_FOUND"
        )

    # ---------- PUT /books/{id} ---------- #
    def test_update_book_success(self):
        book_id = self.client.post("/v1/books", json=self.payload()) \
                             .json()["data"]["id"]

        new_payload = self.payload(title="Clean Architecture", year=2017)
        res = self.client.put(f"/v1/books/{book_id}", json=new_payload)
        self.assertEqual(res.status_code, 200)
        book = res.json()["data"]
        self.assertEqual(book["title"], "Clean Architecture")
        self.assertEqual(book["year"], 2017)

    def test_update_book_not_found(self):
        fake = "22222222-2222-2222-2222-222222222222"
        res = self.client.put(f"/v1/books/{fake}", json=self.payload())
        self.assertEqual(res.status_code, 404)

    # ---------- DELETE /books/{id} ---------- #
    def test_delete_book_success(self):
        book_id = self.client.post("/v1/books", json=self.payload()) \
                             .json()["data"]["id"]

        res = self.client.delete(f"/v1/books/{book_id}")
        self.assertEqual(res.status_code, 204)

        # ya no existe
        res = self.client.get(f"/v1/books/{book_id}")
        self.assertEqual(res.status_code, 404)

    def test_delete_book_not_found(self):
        fake = "33333333-3333-3333-3333-333333333333"
        res = self.client.delete(f"/v1/books/{fake}")
        self.assertEqual(res.status_code, 404)

    # ---------- OPENAPI ---------- #
    def test_openapi_schema_version(self):
        res = self.client.get("/openapi.json")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["openapi"], "3.0.3")
        self.assertEqual(data["info"]["title"], "Books API")

