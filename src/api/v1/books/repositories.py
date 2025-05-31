from db.posgresql import get_db_context
from db.posgresql.models.public import Book
from api.v1.books.schema import BookCreateSchema
from sqlalchemy import select

class BookRepository:

    @staticmethod
    def get_all() -> tuple[bool, list[Book]]:
        with get_db_context() as session:
            books = session.scalars(select(Book)).all()
            return True, books

    @staticmethod
    def get_by_id(book_id: int) -> tuple[bool, Book | None]:
        with get_db_context() as session:
            book = session.get(Book, book_id)
            return (True, book) if book else (False, None)

    @staticmethod
    def create(book_create: BookCreateSchema) -> tuple[bool, Book]:
        with get_db_context() as session:
            new_book = Book(**book_create.model_dump())
            session.add(new_book)
            session.commit()
            session.refresh(new_book)
            return True, new_book

    @staticmethod
    def update(book_id: int, book_update: BookCreateSchema) -> tuple[bool, Book | None]:
        with get_db_context() as session:
            book = session.get(Book, book_id)
            if not book:
                return False, None
            for key, value in book_update.model_dump().items():
                setattr(book, key, value)
            session.commit()
            session.refresh(book)
            return True, book

    @staticmethod
    def delete(book_id: int) -> tuple[bool, None]:
        with get_db_context() as session:
            book = session.get(Book, book_id)
            if not book:
                return False, None
            session.delete(book)
            session.commit()
            return True, None
