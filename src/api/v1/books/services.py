from api.v1.books.repositories import BookRepository
from api.v1.books.schema import BookSchema, BookCreateSchema
from core.exceptions import BookException
from uuid import UUID


class BooksListService:
    @staticmethod
    def list() -> list[BookSchema]:
        success, list_books = BookRepository.get_all()
        if not success:
            raise BookException(message="Failed to retrieve books")
        return [BookSchema(**book.to_dict()) for book in list_books]


class BookCreateService:
    @staticmethod
    def create(book_data: BookCreateSchema) -> BookSchema:
        success, new_book = BookRepository.create(book_data)
        if not success:
            raise BookException(message="Failed to create book")
        return BookSchema(**new_book.to_dict())


class BookRetrieveService:
    @staticmethod
    def retrieve(book_id: UUID) -> BookSchema:
        success, book = BookRepository.get_by_id(book_id)
        if not success:
            raise BookException(
                message=f"Book with ID {book_id} not found",
                data={"payload": {"book_id": str(book_id)}}
            )
        return BookSchema(**book.to_dict())


class BookUpdateService:
    @staticmethod
    def update(book_id: UUID, book_data: BookCreateSchema) -> BookSchema:
        success, updated_book = BookRepository.update(book_id, book_data)
        if not success:
            raise BookException(
                message=f"Book with ID {book_id} not found for update",
                data={"payload": {"book_id": str(book_id)}}
            )
        return BookSchema(**updated_book.to_dict())


class BookDeleteService:
    @staticmethod
    def delete(book_id: UUID) -> None:
        success, _ = BookRepository.delete(book_id)
        if not success:
            raise BookException(
                message=f"Book with ID {book_id} not found for deletion",
                data={"payload": {"book_id": str(book_id)}}
            )
