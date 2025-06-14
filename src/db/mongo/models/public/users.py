from db.mongo.base import MongoAbstractRepository
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class UserRegistrationState(str, Enum):
    NOT_REGISTERED = "not_registered"
    WAITING_NAME = "waiting_name"
    WAITING_AGE = "waiting_age"
    COMPLETED = "completed"
    EDITING_NAME = "editing_name"
    EDITING_AGE = "editing_age"
    CONFIRMING_DELETE = "confirming_delete"


class UserDocument(BaseModel):
    chat_id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    name: Optional[str] = None  # Nombre que proporciona el usuario
    age: Optional[int] = None
    registration_state: UserRegistrationState = UserRegistrationState.NOT_REGISTERED
    registered_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserMongoRepository(MongoAbstractRepository):
    collection_name = "telegram_users"
    document_model = UserDocument 