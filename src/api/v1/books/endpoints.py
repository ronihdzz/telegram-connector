from api.v1.books.schema import BookCreateSchema
from loguru import logger
from shared.base_responses import create_response_for_fast_api, EnvelopeResponse
from fastapi import APIRouter, Response
from uuid import UUID
from api.v1.books.services import (
    BooksListService,
    BookCreateService,
    BookRetrieveService,
    BookUpdateService,
    BookDeleteService,
)

router = APIRouter(prefix="/books", tags=["Books"])


@router.get("", response_model=EnvelopeResponse)
async def get_books() -> EnvelopeResponse:
    logger.info("Retrieving all books")
    books = BooksListService.list()
    return create_response_for_fast_api(data=books)


@router.post("", response_model=EnvelopeResponse)
async def create_book(book: BookCreateSchema) -> EnvelopeResponse:
    logger.info("Creating new book")
    new_book = BookCreateService.create(book)
    logger.info(f"Book created with ID: {new_book.id}")
    return create_response_for_fast_api(data=new_book, status_code_http=201)


@router.get("/{book_id}", response_model=EnvelopeResponse)
async def get_book(book_id: UUID) -> EnvelopeResponse:
    logger.info(f"Retrieving book with ID: {book_id}")
    book = BookRetrieveService.retrieve(book_id)
    return create_response_for_fast_api(data=book)


@router.put("/{book_id}", response_model=EnvelopeResponse)
async def update_book(book_id: UUID, updated: BookCreateSchema) -> EnvelopeResponse:
    logger.info(f"Updating book with ID: {book_id}")
    updated_book = BookUpdateService.update(book_id, updated)
    logger.info(f"Successfully updated book with ID: {book_id}")
    return create_response_for_fast_api(data=updated_book)


@router.delete("/{book_id}", status_code=204)
async def delete_book(book_id: UUID) -> None:
    logger.info(f"Attempting to delete book with ID: {book_id}")
    BookDeleteService.delete(book_id)
    logger.info(f"Successfully deleted book with ID: {book_id}")
    return Response(status_code=204)
