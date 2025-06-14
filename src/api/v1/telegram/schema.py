from pydantic import BaseModel, Field, ConfigDict, field_serializer
from uuid import UUID
from datetime import datetime
from enum import Enum

# ---------- Estados de registro ----------
class UserRegistrationState(str, Enum):
    NOT_REGISTERED = "not_registered"
    WAITING_NAME = "waiting_name"
    WAITING_AGE = "waiting_age"
    COMPLETED = "completed"
    EDITING_NAME = "editing_name"
    EDITING_AGE = "editing_age"

# ---------- Usuario Schema ----------
class TelegramUserSchema(BaseModel):
    chat_id: int
    user_id: int | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    name: str | None = None
    age: int | None = None
    registration_state: UserRegistrationState = UserRegistrationState.NOT_REGISTERED
    registered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

# ---------- 1. DTO de conexión ----------
class RequestTelegramConnectorCreateSchema(BaseModel):
    bot_user_name: str
    bot_token: str


class TelegramConnectorCreateSchema(BaseModel):
    user_id: UUID
    bot_user_name: str
    bot_token: str
    bot_token_secret: str

class TelegramConnectorCreateResponseSchema(BaseModel):
    id: UUID
    user_id: UUID
    bot_user_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(validate_by_name=False)

    @field_serializer('id')
    def serialize_id(self, v: UUID, _info):
        return str(v)

    @field_serializer('user_id')
    def serialize_user_id(self, v: UUID, _info):
        return str(v)

    @field_serializer('created_at')
    def serialize_created_at(self, v: datetime, _info):
        return v.isoformat()

    @field_serializer('updated_at')
    def serialize_updated_at(self, v: datetime, _info):
        return v.isoformat()


# ---------- 1A. DTO de envío ----------
class SendMessageIn(BaseModel):
    chat_id: int               = Field(..., description="ID del chat destino")
    text:    str               = Field(..., min_length=1, max_length=4096)

class SendMessageOut(BaseModel):
    telegram_message_id: int
    status: str = "sent"

class WebhookMessageReceived(BaseModel):
    date: datetime
    message_id: int
    chat_id: int
    text: str | None = None
    caption: str | None = None
    photo: list[str] | None = None
    sticker: str | None = None
    
    user_id: UUID
    bot_user_name: str
    connector_id: UUID

    model_config = ConfigDict(validate_by_name=False)
    
    @field_serializer('user_id')
    def serialize_user_id(self, v: UUID, _info):
        return str(v)
    
    @field_serializer('connector_id')
    def serialize_connector_id(self, v: UUID, _info):
        return str(v)

class WebhookManagerIn(BaseModel):
    date: datetime
    message_id: int
    chat_id: int
    text: str | None = None
    caption: str | None = None
    photo: list[str] | None = None
    sticker: str | None = None
    