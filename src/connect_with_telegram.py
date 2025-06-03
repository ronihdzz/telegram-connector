import requests, os
from core.settings import settings

TOKEN = settings.TELEGRAM_BOT_TOKEN


WEBHOOK = f"{settings.HOST}/v1/telegram/webhook"
SECRET  = settings.TELEGRAM_SECRET_TOKEN      

resp = requests.post(
    f"https://api.telegram.org/bot{TOKEN}/setWebhook",
    json={"url": WEBHOOK, "secret_token": SECRET}
)
print(resp.json())     