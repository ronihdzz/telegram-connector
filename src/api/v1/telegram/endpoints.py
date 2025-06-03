# endpoints.py
from uuid import UUID
from fastapi import Request, Header, APIRouter
from shared.base_responses import EnvelopeResponse
from api.v1.telegram.schema import SendMessageIn, SendMessageOut, RequestTelegramConnectorCreateSchema
from api.v1.telegram.services import ConnectTelegramService, TelegramWebhookService, SendMessageService

router = APIRouter(prefix="/telegram", tags=["Telegram"])

@router.post("/connect")
async def connect_telegram(
    payload: RequestTelegramConnectorCreateSchema,
    request: Request
) -> EnvelopeResponse:
    return await ConnectTelegramService.connect(payload, request)

@router.post("/webhook/{telegram_connector_id}")
async def telegram_webhook(
        request: Request,
        telegram_connector_id: str,
        x_telegram_bot_api_secret_token: str | None = Header(None)
):
    return await TelegramWebhookService.webhook(request, telegram_connector_id, x_telegram_bot_api_secret_token)

@router.post("/send/{telegram_connector_id}", response_model=SendMessageOut, summary="Enviar mensaje a un chat")
async def send_message(
    telegram_connector_id: UUID,
    payload: SendMessageIn,
    request: Request
) -> EnvelopeResponse:
    return await SendMessageService.send(telegram_connector_id, payload, request)
