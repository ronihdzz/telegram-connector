from core.settings import settings
from loguru import logger
import requests
from fastapi.exceptions import HTTPException



if __name__ == "__main__":
    BOT_MANAGER_TOKEN = settings.BOT_MANAGER_TOKEN

    url = f"https://api.telegram.org/bot{BOT_MANAGER_TOKEN}/setWebhook"
    webhook_url = f"{settings.HOST}/v1/telegram/webhook-manager"
    data = {
        "url": webhook_url,
        "secret_token": settings.BOT_MANAGER_SECRET
    }
    logger.info("Registrando webhook en Telegram...")
    resp = requests.post(url, json=data)
    if resp.status_code != 200:
        logger.error(f"Telegram setWebhook error: {resp.text}")
        raise HTTPException(status_code=500, detail="Error al conectar con Telegram")

    logger.info("Webhook registrado en Telegram correctamente.")
    logger.info("Bot manager registrado en Telegram correctamente.")
