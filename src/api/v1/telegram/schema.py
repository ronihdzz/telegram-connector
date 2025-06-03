from pydantic import BaseModel, Field, ConfigDict, field_serializer
from uuid import UUID
from datetime import datetime

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