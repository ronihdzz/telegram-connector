from sqlalchemy import Column, Integer, String, Enum
from .constants import BookType

from db.posgresql.base import Base, BaseModel

class Book(Base, BaseModel):
    __tablename__ = "books"
    __table_args__ = {"schema": "public"}

    title: str = Column(String, nullable=False)
    author: str = Column(String, nullable=False)
    year: int = Column(Integer, nullable=False)
    type: BookType = Column(Enum(BookType), nullable=False)