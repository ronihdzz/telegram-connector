from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from db.posgresql.base import Base, BaseModel
from sqlalchemy.dialects.postgresql import UUID

class TelegramConnector(Base, BaseModel):
    __tablename__ = "telegram_connectors"
    __table_args__ = {"schema": "public"}

    user_id = Column(UUID, nullable=False)
    bot_user_name = Column(String, nullable=False)
    bot_token = Column(String, nullable=False)
    bot_token_secret = Column(String, nullable=False)
    
