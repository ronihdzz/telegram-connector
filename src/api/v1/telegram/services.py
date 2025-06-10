from __future__ import annotations
from uuid import UUID
from fastapi import Request, HTTPException, status
from core.settings import settings
from api.v1.telegram.schema import (
    SendMessageIn,
    SendMessageOut,
    RequestTelegramConnectorCreateSchema,
    TelegramConnectorCreateSchema,
    WebhookMessageReceived,
    TelegramConnectorCreateResponseSchema
)
import requests
import secrets
from api.v1.telegram.repositories import TelegramConnectorRepository
from shared.base_responses import create_response_for_fast_api, EnvelopeResponse
from datetime import datetime
from loguru import logger
from typing import Any

# --- Utilidades internas seguras ---

def _get_header(headers: dict[str, Any], key: str, required_msg: str) -> str:
    value = headers.get(key)
    if not value:
        logger.error(f"Header missing: {key}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=required_msg)
    return value

def _log_connector(connector: Any, context: str = "") -> None:
    safe = {
        "id": connector.id,
        "user_id": connector.user_id,
        "bot_user_name": connector.bot_user_name,
        "created_at": str(connector.created_at),
        "updated_at": str(connector.updated_at)
    }
    logger.info(f"{context}Connector info: {safe}")

def _raise_and_log(detail: str, status_code: int = 400) -> None:
    logger.error(detail)
    raise HTTPException(status_code=status_code, detail=detail)

class ConnectTelegramService:
    @staticmethod
    async def connect(
        payload: RequestTelegramConnectorCreateSchema,
        request: Request
    ) -> EnvelopeResponse:
        headers = request.headers

        api_key = _get_header(headers, "X-Api-Key", "API Key is required")
        if api_key != settings.API_KEY:
            _raise_and_log("Invalid API Key", status.HTTP_400_BAD_REQUEST)

        user_id = _get_header(headers, "X-User-Id", "User ID is required")

        # Crea el secret SIN loguear el valor
        secret_token = secrets.token_urlsafe(192)
        created, telegram_connector = TelegramConnectorRepository.create(
            TelegramConnectorCreateSchema(
                user_id=user_id,
                bot_user_name=payload.bot_user_name,
                bot_token=payload.bot_token,
                bot_token_secret=secret_token
            )
        )
        if not created:
            _raise_and_log("Error al crear el conector de Telegram", status.HTTP_500_INTERNAL_SERVER_ERROR)
        _log_connector(telegram_connector, context="[Create] ")

        # Nunca logues el token, solo la operación
        url = f"https://api.telegram.org/bot{payload.bot_token}/setWebhook"
        webhook_url = f"{settings.HOST}/v1/telegram/webhook/{telegram_connector.id}"
        data = {
            "url": webhook_url,
            "secret_token": secret_token
        }
        logger.info("Registrando webhook en Telegram...")
        resp = requests.post(url, json=data)
        if resp.status_code != 200:
            logger.error(f"Telegram setWebhook error: {resp.text}")
            raise HTTPException(status_code=500, detail="Error al conectar con Telegram")
        logger.info("Webhook registrado en Telegram correctamente.")

        data_response = TelegramConnectorCreateResponseSchema(
            id=telegram_connector.id,
            user_id=telegram_connector.user_id,
            bot_user_name=telegram_connector.bot_user_name,
            created_at=telegram_connector.created_at,
            updated_at=telegram_connector.updated_at
        )
        return create_response_for_fast_api(data=data_response.model_dump(mode="json"))

class TelegramWebhookService:
    @staticmethod
    async def webhook(
        request: Request,
        telegram_connector_id: str,
        x_telegram_bot_api_secret_token: str | None
    ) -> dict[str, str]:
        logger.info("📥 Webhook recibido")
        logger.info(f"ID recibido: {telegram_connector_id}")

        exists, telegram_connector = TelegramConnectorRepository.get_by_id(telegram_connector_id)
        if not exists or telegram_connector is None:
            _raise_and_log("Telegram connector not found", status.HTTP_404_NOT_FOUND)
        _log_connector(telegram_connector, context="[Webhook] ")

        # Nunca logues secretos ni tokens completos
        if x_telegram_bot_api_secret_token != telegram_connector.bot_token_secret:
            logger.warning("Token inválido en webhook (NO SE MUESTRA POR SEGURIDAD)")
            raise HTTPException(status_code=403, detail="Invalid secret")
        logger.info("Token válido (secreto verificado)")

        message_received = await request.json()
        logger.debug(f"message_received: {str(message_received)[:500]}")  # Loguea máx 500 chars

        message = message_received.get("message") or message_received.get("edited_message")
        if not message:
            logger.info("⚠️ Update ignorado - no es un mensaje")
            return {"status": "ignored"}

        # Procesa y loguea solo IDs/textos, nunca attachments
        chat_id = message.get("chat", {}).get("id")
        webhook_message_received = WebhookMessageReceived(
            user_id=telegram_connector.user_id,
            bot_user_name=telegram_connector.bot_user_name,
            message_id=message.get("message_id"),
            date=datetime.fromtimestamp(message.get("date", 0)),
            text=message.get("text"),
            caption=message.get("caption"),
            photo=message.get("photo"),
            sticker=message.get("sticker"),
            connector_id=telegram_connector.id,
            chat_id=chat_id
        )

        logger.info(f"Recibido message_id={webhook_message_received.message_id} chat_id={chat_id} user_id={webhook_message_received.user_id}")

        # Dispara webhook
        headers = {"X-User-Id": str(webhook_message_received.user_id)}
        logger.info(f"Enviando mensaje recibido a backend destino")
        resp = requests.post(
            settings.WEBHOOK_MESSAGE_RECEIVED,
            json=webhook_message_received.model_dump(mode="json"),
            headers=headers,
            timeout=5
        )
        if resp.status_code != 200:
            logger.error(f"Error al enviar webhook: {resp.text}")
        else:
            logger.info("Webhook entregado correctamente")

        return {"status": "ok"}

class SendMessageService:
    @staticmethod
    async def send(
        telegram_connector_id: UUID,
        payload: SendMessageIn,
        request: Request
    ) -> EnvelopeResponse:
        headers = request.headers

        api_key = _get_header(headers, "X-Api-Key", "API Key is required")
        if api_key != settings.API_KEY:
            _raise_and_log("Invalid API Key", status.HTTP_400_BAD_REQUEST)

        user_id = _get_header(headers, "X-User-Id", "User ID is required")

        exists, telegram_connector = TelegramConnectorRepository.get_by_id(telegram_connector_id)
        if not exists or telegram_connector is None:
            _raise_and_log("Telegram connector not found", status.HTTP_404_NOT_FOUND)
        _log_connector(telegram_connector, context="[Send] ")

        user_id_message = str(telegram_connector.user_id)
        if user_id_message != user_id:
            _raise_and_log("Telegram message not found", status.HTTP_403_FORBIDDEN)

        logger.info(f"Enviando mensaje a chat_id={payload.chat_id} con el bot {telegram_connector.bot_user_name}")
        TG_API = f"https://api.telegram.org/bot{telegram_connector.bot_token}"
        r = requests.post(
            f"{TG_API}/sendMessage",
            json={"chat_id": payload.chat_id, "text": payload.text},
            timeout=10
        )
        data = r.json()
        logger.debug(f"Respuesta de Telegram: {str(data)[:400]}")  # Nunca logues texto completo si hay attachments

        if not data.get("ok"):
            logger.error(f"Telegram error: {data.get('description', 'Unknown error')}")
            raise HTTPException(status_code=502, detail=data.get("description"))

        logger.info(f"Mensaje enviado correctamente, message_id={data['result']['message_id']}")
        data_response = SendMessageOut(
            telegram_message_id=data["result"]["message_id"],
            status="sent"
        )
        return create_response_for_fast_api(data=data_response.model_dump(mode="json"))
