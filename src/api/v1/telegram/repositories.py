from db.posgresql import get_db_context
from db.posgresql.models.public import TelegramConnector
from api.v1.telegram.schema import TelegramConnectorCreateSchema
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from uuid import UUID

class TelegramConnectorRepository:

    @staticmethod
    def get_all() -> tuple[bool, list[TelegramConnector]]:
        with get_db_context() as session:
            telegram_connectors = session.scalars(select(TelegramConnector)).all()
            return True, telegram_connectors
    
    @staticmethod
    def get_by_user_id(user_id: UUID) -> tuple[bool, list[TelegramConnector]]:
        with get_db_context() as session:
            telegram_connectors = session.scalars(select(TelegramConnector).where(TelegramConnector.user_id == user_id)).all()
            return True, telegram_connectors
    
    @staticmethod
    def get_by_id(telegram_connector_id: UUID) -> tuple[bool, TelegramConnector]:
        with get_db_context() as session:
            telegram_connector = session.scalars(select(TelegramConnector).where(TelegramConnector.id == telegram_connector_id)).first()
            return True, telegram_connector

    @staticmethod
    def create(telegram_connector_create: TelegramConnectorCreateSchema) -> tuple[bool, TelegramConnector]:
        with get_db_context() as session:
            new_telegram_connector = TelegramConnector(**telegram_connector_create.model_dump())
            session.add(new_telegram_connector)
            session.commit()
            session.refresh(new_telegram_connector)
            return True, new_telegram_connector


    @staticmethod
    def delete(bot_user_name: str) -> tuple[bool, None]:
        with get_db_context() as session:
            telegram_connector = session.scalars(select(TelegramConnector).where(TelegramConnector.bot_user_name == bot_user_name)).first()
            if not telegram_connector:
                return False, None
            session.delete(telegram_connector)
            session.commit()
            return True, None
        

   