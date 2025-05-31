from pydantic import BaseModel, ConfigDict, field_serializer
from db.posgresql.models.public import BookType
from uuid import UUID

# Data model
class BookSchema(BaseModel):
    id: UUID
    title: str
    author: str
    year: int
    type: BookType

    model_config = ConfigDict(validate_by_name=False)

    @field_serializer('id')
    def serialize_id(self, v: UUID, _info):
        return str(v)

# Create a new book
class BookCreateSchema(BaseModel):
    title: str
    author: str
    year: int
    type: BookType