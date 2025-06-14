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
    TelegramConnectorCreateResponseSchema,
    WebhookManagerIn,
    TelegramUserSchema,
    UserRegistrationState
)
import requests
import secrets
from api.v1.telegram.repositories import TelegramConnectorRepository
from shared.base_responses import create_response_for_fast_api, EnvelopeResponse
from datetime import datetime
from loguru import logger
from typing import Any
import json

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
        logger.debug(f"message_received: {str(message_received)[:500]}")

        # Verificar si es un callback query (botón presionado)
        callback_query = message_received.get("callback_query")
        if callback_query:
            await TelegramWebhookManagerService._handle_callback_query(callback_query)
            return {"status": "ok"}

        # Verificar si es un mensaje o mensaje editado
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



# Simulación de base de datos con diccionario (más tarde se reemplazará por MongoDB)
users_db = {}

class TelegramWebhookManagerService:
    
    @staticmethod
    def _send_message_to_telegram(chat_id: int, text: str, reply_markup: dict = None) -> dict:
        """Envía un mensaje a Telegram con opciones de teclado inline"""
        TG_API = f"https://api.telegram.org/bot{settings.BOT_MANAGER_TOKEN}"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
            
        logger.info(f"Enviando mensaje a chat_id={chat_id}")
        r = requests.post(f"{TG_API}/sendMessage", json=payload, timeout=10)
        data = r.json()
        
        if not data.get("ok"):
            logger.error(f"Telegram error: {data.get('description', 'Unknown error')}")
            raise HTTPException(status_code=502, detail=data.get("description"))
        
        logger.info(f"Mensaje enviado correctamente, message_id={data['result']['message_id']}")
        return data
    
    @staticmethod
    def _send_message_with_keyboard(chat_id: int, text: str, keyboard: dict = None) -> dict:
        """Envía un mensaje con teclado personalizado (ReplyKeyboardMarkup)"""
        TG_API = f"https://api.telegram.org/bot{settings.BOT_MANAGER_TOKEN}"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if keyboard:
            payload["reply_markup"] = keyboard
            
        logger.info(f"Enviando mensaje con teclado personalizado a chat_id={chat_id}")
        r = requests.post(f"{TG_API}/sendMessage", json=payload, timeout=10)
        data = r.json()
        
        if not data.get("ok"):
            logger.error(f"Telegram error: {data.get('description', 'Unknown error')}")
            raise HTTPException(status_code=502, detail=data.get("description"))
        
        logger.info(f"Mensaje con teclado enviado correctamente, message_id={data['result']['message_id']}")
        return data
    
    @staticmethod
    def _get_user(chat_id: int) -> TelegramUserSchema | None:
        """Obtiene un usuario del diccionario simulado"""
        return users_db.get(chat_id)
    
    @staticmethod
    def _save_user(user: TelegramUserSchema):
        """Guarda un usuario en el diccionario simulado"""
        users_db[user.chat_id] = user
        logger.info(f"Usuario guardado: chat_id={user.chat_id}, estado={user.registration_state}")
    
    @staticmethod
    def _create_main_menu_keyboard():
        """Crea el teclado principal simplificado"""
        return {
            "keyboard": [
                [{"text": "👤 Perfil"}, {"text": "⚙️ Settings"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
    
    @staticmethod
    def _create_webapp_keyboard():
        """Crea el teclado personalizado con Mini Apps (ReplyKeyboardMarkup)"""
        webapp_base_url = settings.WEBAPP_BASE_URL
        
        return {
            "keyboard": [
                [
                    {
                        "text": "🏋️ Rutina Completa", 
                        "web_app": {"url": f"{webapp_base_url}/rutina-completa"}
                    }
                ],
                [
                    {
                        "text": "👤 Perfil Avanzado", 
                        "web_app": {"url": f"{webapp_base_url}/perfil-avanzado"}
                    }
                ],
                [
                    {
                        "text": "📊 Dashboard", 
                        "web_app": {"url": f"{webapp_base_url}/dashboard"}
                    }
                ],
                [
                    {"text": "🔙 Menú Principal"}
                ]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False,
            "input_field_placeholder": "Elige una opción o usa las Mini Apps..."
        }
    
    @staticmethod
    def _create_profile_edit_keyboard():
        """Crea el teclado para editar perfil"""
        return {
            "inline_keyboard": [
                [{"text": "✏️ Editar Nombre", "callback_data": "edit_name"}],
                [{"text": "🎂 Editar Edad", "callback_data": "edit_age"}],
                [{"text": "🗑️ Eliminar Perfil", "callback_data": "delete_profile"}],
                [{"text": "🔙 Volver al Menú", "callback_data": "back_to_menu"}]
            ]
        }
    
    @staticmethod
    def _create_delete_confirmation_keyboard():
        """Crea el teclado de confirmación para eliminar perfil"""
        return {
            "inline_keyboard": [
                [{"text": "❌ SÍ, ELIMINAR", "callback_data": "confirm_delete"}],
                [{"text": "✅ NO, CANCELAR", "callback_data": "cancel_delete"}]
            ]
        }

    @staticmethod
    def _create_registration_keyboard():
        """Crea el teclado para registro con Mini Web App"""
        webapp_base_url = settings.WEBAPP_BASE_URL
        return {
            "inline_keyboard": [
                [
                    {
                        "text": "✨ ¡Completar Registro!",
                        "web_app": {"url": f"{webapp_base_url}/registro"}
                    }
                ],
                [
                    {"text": "ℹ️ ¿Qué es esto?", "callback_data": "info_registro"}
                ]
            ]
        }

    @staticmethod
    def _show_registration_webapp(chat_id: int, first_name: str):
        """Muestra la Mini Web App de registro"""
        message = (
            f"╭─────────────────────────╮\n"
            f"│  <b>🎉 ¡EXCELENTE! 🎉</b>  │\n"
            f"╰─────────────────────────╯\n\n"
            f"✨ <b>¡Perfecto {first_name}!</b> ✨\n\n"
            f"🚀 <b>Ahora vamos a registrarte</b>\n"
            f"<b>con nuestro formulario</b>\n"
            f"<b>súper fácil y rápido</b>\n\n"
            f"📱 <b>Características:</b>\n"
            f"• 🎨 Interfaz moderna y elegante\n"
            f"• ⚡ Validación en tiempo real\n"
            f"• 🔄 Progreso visual\n"
            f"• 🎉 Animaciones fluidas\n\n"
            f"┌─────────────────────────┐\n"
            f"│ 👆 <b>Toca el botón de abajo</b>  │\n"
            f"│   <b>para abrir el formulario</b>  │\n"
            f"└─────────────────────────┘"
        )
        keyboard = TelegramWebhookManagerService._create_registration_keyboard()
        TelegramWebhookManagerService._send_message_with_keyboard(chat_id, message, keyboard)
    
    @staticmethod
    def _handle_not_registered_user(chat_id: int, text: str, from_user: dict):
        """Maneja usuarios no registrados - ahora usa Mini Web App"""
        if text and text.lower() == "/registrar":
            # Crear usuario en estado de preparación para registrarse
            user = TelegramUserSchema(
                chat_id=chat_id,
                user_id=from_user.get("id"),
                username=from_user.get("username"),
                first_name=from_user.get("first_name"),
                last_name=from_user.get("last_name"),
                registration_state=UserRegistrationState.NOT_REGISTERED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            TelegramWebhookManagerService._save_user(user)
            
            # Mostrar Mini Web App de registro
            TelegramWebhookManagerService._show_registration_webapp(chat_id, from_user.get("first_name", "Usuario"))
        else:
            # Usuario no registrado, mostrar bienvenida con Mini Web App
            first_name = from_user.get("first_name", "Usuario")
            message = (
                f"👋 <b>Hola {first_name}!</b>\n\n"
                f"🏋️ <b>Bienvenido a GymBot</b>\n\n"
                f"Para empezar necesitas registrarte:"
            )
            # Crear teclado con botón de registro usando Mini Web App
            keyboard = TelegramWebhookManagerService._create_registration_keyboard()
            TelegramWebhookManagerService._send_message_with_keyboard(chat_id, message, keyboard)
    
    @staticmethod
    def _handle_waiting_name(chat_id: int, text: str, user: TelegramUserSchema):
        """Redirige al registro con Mini Web App - método legacy"""
        message = (
            f"╭─────────────────────────╮\n"
            f"│  <b>🚀 NUEVO REGISTRO 🚀</b>  │\n"
            f"╰─────────────────────────╯\n\n"
            f"✨ <b>¡Ahora tenemos un nuevo</b>\n"
            f"<b>sistema de registro!</b> ✨\n\n"
            f"🎯 <b>Más fácil, rápido y elegante</b>\n\n"
            f"┌─────────────────────────┐\n"
            f"│ 👆 <b>Usa el botón de abajo</b>  │\n"
            f"│   <b>para registrarte</b>     │\n"
            f"└─────────────────────────┘"
        )
        keyboard = TelegramWebhookManagerService._create_registration_keyboard()
        TelegramWebhookManagerService._send_message_with_keyboard(chat_id, message, keyboard)
    
    @staticmethod
    def _handle_waiting_age(chat_id: int, text: str, user: TelegramUserSchema):
        """Redirige al registro con Mini Web App - método legacy"""
        message = (
            f"╭─────────────────────────╮\n"
            f"│  <b>🚀 NUEVO REGISTRO 🚀</b>  │\n"
            f"╰─────────────────────────╯\n\n"
            f"✨ <b>¡Ahora tenemos un nuevo</b>\n"
            f"<b>sistema de registro!</b> ✨\n\n"
            f"🎯 <b>Más fácil, rápido y elegante</b>\n\n"
            f"┌─────────────────────────┐\n"
            f"│ 👆 <b>Usa el botón de abajo</b>  │\n"
            f"│   <b>para registrarte</b>     │\n"
            f"└─────────────────────────┘"
        )
        keyboard = TelegramWebhookManagerService._create_registration_keyboard()
        TelegramWebhookManagerService._send_message_with_keyboard(chat_id, message, keyboard)
    
    @staticmethod
    def _handle_registered_user(chat_id: int, text: str, user: TelegramUserSchema):
        """Maneja usuarios ya registrados"""
        # Manejar botones del teclado
        if text == "👤 Perfil":
            TelegramWebhookManagerService._show_user_profile(chat_id, user)
            return
        elif text == "⚙️ Settings":
            TelegramWebhookManagerService._show_settings(chat_id, user)
            return
        
        # Mensaje de saludo simplificado
        greeting_message = (
            f"Hola buenas <b>{user.name}</b> ¿qué deseas hacer?"
        )
        keyboard = TelegramWebhookManagerService._create_main_menu_keyboard()
        TelegramWebhookManagerService._send_message_with_keyboard(chat_id, greeting_message, keyboard)
    
    @staticmethod
    def _show_user_profile(chat_id: int, user: TelegramUserSchema):
        """Muestra el perfil del usuario"""
        registered_date = user.registered_at.strftime("%d/%m/%Y a las %H:%M") if user.registered_at else "No disponible"
        
        # Perfil simplificado
        profile_message = (
            f"👤 <b>Mi Perfil</b>\n\n"
            f"<b>Nombre:</b> {user.name}\n"
            f"<b>Edad:</b> {user.age} años\n"
            f"<b>Chat ID:</b> {user.chat_id}\n"
            f"<b>Registrado:</b> {registered_date}"
        )
        
        keyboard = TelegramWebhookManagerService._create_main_menu_keyboard()
        TelegramWebhookManagerService._send_message_with_keyboard(chat_id, profile_message, keyboard)

    @staticmethod
    def _show_settings(chat_id: int, user: TelegramUserSchema):
        """Muestra la webapp de settings"""
        webapp_base_url = settings.WEBAPP_BASE_URL
        
        message = (
            f"⚙️ <b>Settings</b>\n\n"
            f"Configura tu cuenta y preferencias:"
        )
        
        keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "⚙️ Abrir Settings",
                        "web_app": {"url": f"{webapp_base_url}/settings"}
                    }
                ]
            ]
        }
        
        TelegramWebhookManagerService._send_message_to_telegram(chat_id, message, keyboard)
    
    @staticmethod
    def _show_edit_options(chat_id: int, user: TelegramUserSchema):
        """Muestra las opciones de edición"""
        edit_message = (
            f"╭─────────────────────────╮\n"
            f"│   <b>⚙️ EDITAR PERFIL ⚙️</b>   │\n"
            f"╰─────────────────────────╯\n\n"
            f"📋 <b>Información actual:</b>\n\n"
            f"🏷️ <b>Nombre:</b> <i>{user.name}</i>\n"
            f"🎂 <b>Edad:</b> <i>{user.age} años</i>\n\n"
            f"┌─────────────────────────┐\n"
            f"│     ¿Qué deseas modificar?    │\n"
            f"└─────────────────────────┘"
        )
        
        keyboard = TelegramWebhookManagerService._create_profile_edit_keyboard()
        TelegramWebhookManagerService._send_message_to_telegram(chat_id, edit_message, keyboard)
    
    @staticmethod
    def _handle_editing_name(chat_id: int, text: str, user: TelegramUserSchema):
        """Maneja la edición del nombre"""
        if not text or len(text.strip()) < 2:
            message = "Por favor, ingresa un nombre válido (mínimo 2 caracteres):"
            TelegramWebhookManagerService._send_message_to_telegram(chat_id, message)
            return
        
        old_name = user.name
        user.name = text.strip()
        user.registration_state = UserRegistrationState.COMPLETED
        user.updated_at = datetime.utcnow()
        TelegramWebhookManagerService._save_user(user)
        
        success_message = (
            f"✅ <b>Nombre actualizado correctamente</b>\n\n"
            f"📝 Nombre anterior: {old_name}\n"
            f"📝 Nombre nuevo: {user.name}\n\n"
            f"¿Qué deseas hacer ahora?"
        )
        
        keyboard = TelegramWebhookManagerService._create_main_menu_keyboard()
        TelegramWebhookManagerService._send_message_to_telegram(chat_id, success_message, keyboard)
    
    @staticmethod
    def _handle_editing_age(chat_id: int, text: str, user: TelegramUserSchema):
        """Maneja la edición de la edad"""
        try:
            age = int(text.strip())
            if age < 13 or age > 120:
                message = "Por favor, ingresa una edad válida (entre 13 y 120 años):"
                TelegramWebhookManagerService._send_message_to_telegram(chat_id, message)
                return
            
            old_age = user.age
            user.age = age
            user.registration_state = UserRegistrationState.COMPLETED
            user.updated_at = datetime.utcnow()
            TelegramWebhookManagerService._save_user(user)
            
            success_message = (
                f"✅ <b>Edad actualizada correctamente</b>\n\n"
                f"🎂 Edad anterior: {old_age} años\n"
                f"🎂 Edad nueva: {user.age} años\n\n"
                f"¿Qué deseas hacer ahora?"
            )
            
            keyboard = TelegramWebhookManagerService._create_main_menu_keyboard()
            TelegramWebhookManagerService._send_message_to_telegram(chat_id, success_message, keyboard)
            
        except ValueError:
            message = "Por favor, ingresa solo números para tu edad:"
            TelegramWebhookManagerService._send_message_to_telegram(chat_id, message)
    
    @staticmethod
    def _show_delete_confirmation(chat_id: int, user: TelegramUserSchema):
        """Muestra la confirmación de eliminación de perfil"""
        warning_message = (
            f"╭─────────────────────────╮\n"
            f"│    <b>⚠️ ADVERTENCIA ⚠️</b>    │\n"
            f"╰─────────────────────────╯\n\n"
            f"🚨 <b>¿Estás seguro de que deseas</b>\n"
            f"<b>eliminar tu perfil completamente?</b>\n\n"
            f"📋 <b>Se perderá la siguiente información:</b>\n"
            f"• Nombre: <i>{user.name}</i>\n"
            f"• Edad: <i>{user.age} años</i>\n"
            f"• Fecha de registro\n"
            f"• Historial de actividad\n\n"
            f"┌─────────────────────────┐\n"
            f"│ ⚠️ <b>Esta acción NO se puede</b>  │\n"
            f"│      <b>deshacer</b> ⚠️       │\n"
            f"└─────────────────────────┘\n\n"
            f"¿Confirmas la eliminación?"
        )
        
        keyboard = TelegramWebhookManagerService._create_delete_confirmation_keyboard()
        TelegramWebhookManagerService._send_message_to_telegram(chat_id, warning_message, keyboard)
    
    @staticmethod
    def _delete_user_profile(chat_id: int):
        """Elimina el perfil del usuario"""
        if chat_id in users_db:
            del users_db[chat_id]
            logger.info(f"Perfil eliminado para chat_id={chat_id}")
        
        farewell_message = (
            f"╭─────────────────────────╮\n"
            f"│   <b>👋 PERFIL ELIMINADO</b>   │\n"
            f"╰─────────────────────────╯\n\n"
            f"✅ <b>Tu perfil ha sido eliminado</b>\n"
            f"<b>exitosamente del sistema.</b>\n\n"
            f"💔 Lamentamos verte partir...\n\n"
            f"🔄 <b>Si cambias de opinión,</b>\n"
            f"puedes volver a registrarte\n"
            f"en cualquier momento escribiendo:\n"
            f"<code>/registrar</code>\n\n"
            f"┌─────────────────────────┐\n"
            f"│  🙏 <i>¡Gracias por haber sido</i>  │\n"
            f"│     <i>parte de nosotros!</i>     │\n"
            f"└─────────────────────────┘"
        )
        
        TelegramWebhookManagerService._send_message_to_telegram(chat_id, farewell_message)

    @staticmethod
    async def webhook_manager(
        request: Request,
        x_telegram_bot_api_secret_token: str | None
    ) -> dict[str, str]:
        logger.info("📥 Webhook recibido")

        # Verificación del token secreto
        if x_telegram_bot_api_secret_token != settings.BOT_MANAGER_SECRET:
            logger.warning("Token inválido en webhook (NO SE MUESTRA POR SEGURIDAD)")
            raise HTTPException(status_code=403, detail="Invalid secret")
        logger.info("Token válido (secreto verificado)")

        message_received = await request.json()
        logger.debug(f"message_received: {str(message_received)[:500]}")

        # Verificar si es un callback query (botón presionado)
        callback_query = message_received.get("callback_query")
        if callback_query:
            await TelegramWebhookManagerService._handle_callback_query(callback_query)
            return {"status": "ok"}

        # Verificar si es un mensaje o mensaje editado
        message = message_received.get("message") or message_received.get("edited_message")
        if not message:
            logger.info("⚠️ Update ignorado - no es un mensaje")
            return {"status": "ignored"}

        # Verificar si es un mensaje con datos de webapp
        if message.get("web_app_data"):
            chat_id = message.get("chat", {}).get("id")
            from_user = message.get("from", {})
            user = TelegramWebhookManagerService._get_user(chat_id)
            
            # Si no existe usuario, crearlo para el registro
            if not user:
                user = TelegramUserSchema(
                    chat_id=chat_id,
                    user_id=from_user.get("id"),
                    username=from_user.get("username"),
                    first_name=from_user.get("first_name"),
                    last_name=from_user.get("last_name"),
                    registration_state=UserRegistrationState.NOT_REGISTERED,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                TelegramWebhookManagerService._save_user(user)
            
            TelegramWebhookManagerService._handle_webapp_data(chat_id, message["web_app_data"], user)
            return {"status": "ok"}

        # Extraer información del mensaje
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "").strip()
        from_user = message.get("from", {})
        
        logger.info(f"Recibido message_id={message.get('message_id')} chat_id={chat_id} text='{text[:50]}...'")

        # Obtener usuario existente o None
        user = TelegramWebhookManagerService._get_user(chat_id)
        
        try:
            if not user:
                # Usuario no registrado
                TelegramWebhookManagerService._handle_not_registered_user(chat_id, text, from_user)
            elif user.registration_state == UserRegistrationState.WAITING_NAME:
                # Esperando nombre
                TelegramWebhookManagerService._handle_waiting_name(chat_id, text, user)
            elif user.registration_state == UserRegistrationState.WAITING_AGE:
                # Esperando edad
                TelegramWebhookManagerService._handle_waiting_age(chat_id, text, user)
            elif user.registration_state == UserRegistrationState.EDITING_NAME:
                # Editando nombre
                TelegramWebhookManagerService._handle_editing_name(chat_id, text, user)
            elif user.registration_state == UserRegistrationState.EDITING_AGE:
                # Editando edad
                TelegramWebhookManagerService._handle_editing_age(chat_id, text, user)
            elif user.registration_state == UserRegistrationState.COMPLETED:
                # Usuario completamente registrado
                TelegramWebhookManagerService._handle_registered_user(chat_id, text, user)
            else:
                # Estado no reconocido, resetear
                logger.warning(f"Estado no reconocido: {user.registration_state}")
                TelegramWebhookManagerService._handle_not_registered_user(chat_id, text, from_user)
                
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            error_message = "Lo siento, ocurrió un error procesando tu mensaje. Por favor intenta de nuevo."
            TelegramWebhookManagerService._send_message_to_telegram(chat_id, error_message)

        return {"status": "ok"}

    @staticmethod
    async def _handle_callback_query(callback_query: dict):
        """Maneja los callback queries (botones inline presionados)"""
        callback_data = callback_query.get("data", "")
        chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
        message_id = callback_query.get("message", {}).get("message_id")
        from_user = callback_query.get("from", {})
        
        logger.info(f"Callback recibido: {callback_data} de chat_id={chat_id}")
        
        # Obtener usuario
        user = TelegramWebhookManagerService._get_user(chat_id)
        if not user or user.registration_state != UserRegistrationState.COMPLETED:
            error_message = "❌ Usuario no registrado. Usa /registrar para comenzar."
            TelegramWebhookManagerService._send_message_to_telegram(chat_id, error_message)
            return
        
        # Responder al callback query para quitar el "loading" del botón
        await TelegramWebhookManagerService._answer_callback_query(callback_query.get("id"))
        
        # Manejar diferentes callbacks
        if callback_data == "my_profile":
            TelegramWebhookManagerService._show_user_profile(chat_id, user)
        elif callback_data == "edit_profile":
            TelegramWebhookManagerService._show_edit_options(chat_id, user)
        elif callback_data == "edit_name":
            user.registration_state = UserRegistrationState.EDITING_NAME
            user.updated_at = datetime.utcnow()
            TelegramWebhookManagerService._save_user(user)
            
            message = (
                f"✏️ <b>Editando tu nombre</b>\n\n"
                f"📝 <b>Nombre actual:</b> {user.name}\n\n"
                f"Por favor, escribe tu nuevo nombre:"
            )
            TelegramWebhookManagerService._send_message_to_telegram(chat_id, message)
        elif callback_data == "edit_age":
            user.registration_state = UserRegistrationState.EDITING_AGE
            user.updated_at = datetime.utcnow()
            TelegramWebhookManagerService._save_user(user)
            
            message = (
                f"🎂 <b>Editando tu edad</b>\n\n"
                f"🎂 <b>Edad actual:</b> {user.age} años\n\n"
                f"Por favor, escribe tu nueva edad (solo números):"
            )
            TelegramWebhookManagerService._send_message_to_telegram(chat_id, message)
        elif callback_data == "delete_profile":
            TelegramWebhookManagerService._show_delete_confirmation(chat_id, user)
        elif callback_data == "confirm_delete":
            TelegramWebhookManagerService._delete_user_profile(chat_id)
        elif callback_data == "cancel_delete":
            cancel_message = (
                f"✅ <b>Eliminación cancelada</b>\n\n"
                f"🛡️ Tu perfil está seguro.\n"
                f"¿Qué deseas hacer ahora?"
            )
            keyboard = TelegramWebhookManagerService._create_main_menu_keyboard()
            TelegramWebhookManagerService._send_message_to_telegram(chat_id, cancel_message, keyboard)
        elif callback_data == "back_to_menu":
            greeting_message = (
                f"╭─────────────────────────╮\n"
                f"│  <b>👋 ¡HOLA {user.name.upper()}! 👋</b>  │\n"
                f"╰─────────────────────────╯\n\n"
                f"🌟 <b>¡Bienvenido de vuelta!</b> 🌟\n\n"
                f"💪 <b>¿Listo para entrenar hoy?</b>\n\n"
                f"┌─────────────────────────┐\n"
                f"│   🎯 <b>¿Qué deseas hacer?</b>   │\n"
                f"└─────────────────────────┘"
            )
            keyboard = TelegramWebhookManagerService._create_main_menu_keyboard()
            TelegramWebhookManagerService._send_message_to_telegram(chat_id, greeting_message, keyboard)
        elif callback_data == "show_webapp_keyboard":
            # Mostrar teclado con Mini Apps (ReplyKeyboardMarkup)
            webapp_message = (
                f"╭─────────────────────────╮\n"
                f"│  <b>🎛️ TECLADO MINI APPS</b>  │\n"
                f"╰─────────────────────────╯\n\n"
                f"✨ <b>¡Hola {user.name}!</b> ✨\n\n"
                f"🎯 <b>Ahora tienes acceso al teclado</b>\n"
                f"<b>con Mini Apps integradas:</b>\n\n"
                f"🏋️ <b>Rutina Completa:</b> Formularios avanzados\n"
                f"👤 <b>Perfil Avanzado:</b> Gestión completa\n"
                f"📊 <b>Dashboard:</b> Estadísticas interactivas\n\n"
                f"┌─────────────────────────┐\n"
                f"│ 💡 <i>Usa los botones de abajo</i> │\n"
                f"│    <i>para abrir las Mini Apps</i>   │\n"
                f"└─────────────────────────┘"
            )
            keyboard = TelegramWebhookManagerService._create_webapp_keyboard()
            TelegramWebhookManagerService._send_message_with_keyboard(chat_id, webapp_message, keyboard)
        elif callback_data == "info_registro":
            # Información sobre las Mini Web Apps
            info_message = (
                f"╭─────────────────────────╮\n"
                f"│  <b>ℹ️ MINI WEB APPS ℹ️</b>  │\n"
                f"╰─────────────────────────╯\n\n"
                f"🚀 <b>¿Qué son las Mini Apps?</b>\n\n"
                f"Las Mini Apps son aplicaciones web\n"
                f"integradas directamente en Telegram\n"
                f"que ofrecen una experiencia más\n"
                f"rica e interactiva.\n\n"
                f"✨ <b>Ventajas de nuestro registro:</b>\n"
                f"• 🎨 Interfaz moderna y elegante\n"
                f"• 📱 Diseño responsive para móvil\n"
                f"• ⚡ Validación en tiempo real\n"
                f"• 🔄 Barra de progreso visual\n"
                f"• 🎉 Animaciones fluidas\n"
                f"• 🔒 100% seguro y privado\n\n"
                f"🛡️ <b>Seguridad:</b>\n"
                f"Tus datos nunca salen de Telegram\n"
                f"y están completamente protegidos.\n\n"
                f"┌─────────────────────────┐\n"
                f"│ 🎯 <b>¡Pruébalo ahora mismo!</b> │\n"
                f"└─────────────────────────┘"
            )
            keyboard = TelegramWebhookManagerService._create_registration_keyboard()
            TelegramWebhookManagerService._send_message_with_keyboard(chat_id, info_message, keyboard)
        elif callback_data in ["register_routine", "edit_routine", "view_routine"]:
            # Funcionalidades futuras
            future_message = (
                f"🚧 <b>Funcionalidad en desarrollo</b>\n\n"
                f"La opción <i>'{callback_data.replace('_', ' ').title()}'</i> estará disponible pronto.\n\n"
                f"¡Gracias por tu paciencia! 😊"
            )
            keyboard = TelegramWebhookManagerService._create_main_menu_keyboard()
            TelegramWebhookManagerService._send_message_to_telegram(chat_id, future_message, keyboard)
        else:
            logger.warning(f"Callback no reconocido: {callback_data}")
    
    @staticmethod
    async def _answer_callback_query(callback_query_id: str, text: str = ""):
        """Responde a un callback query para quitar el loading del botón"""
        TG_API = f"https://api.telegram.org/bot{settings.BOT_MANAGER_TOKEN}"
        payload = {
            "callback_query_id": callback_query_id,
            "text": text
        }
        
        r = requests.post(f"{TG_API}/answerCallbackQuery", json=payload, timeout=5)
        if not r.json().get("ok"):
            logger.warning(f"Error respondiendo callback query: {r.text}")

    @staticmethod
    def _handle_webapp_data(chat_id: int, web_app_data: dict, user: TelegramUserSchema):
        """Maneja datos recibidos de las Mini Apps"""
        try:
            # Parsear los datos JSON de la webapp
            data = json.loads(web_app_data.get('data', '{}'))
            webapp_type = data.get('type', 'unknown')
            
            logger.info(f"Datos recibidos de webapp: {data}")
            
            # Verificar si son datos de registro (detectar por la presencia de name y age)
            if 'name' in data and 'age' in data and not webapp_type:
                TelegramWebhookManagerService._handle_registration_data(chat_id, data, user)
            elif data.get('action') == 'delete_account':
                TelegramWebhookManagerService._handle_delete_account(chat_id, data, user)
            elif data.get('action') == 'update_profile':
                TelegramWebhookManagerService._handle_profile_update(chat_id, data, user)
            else:
                # Datos genéricos
                success_message = (
                    f"✅ <b>Datos recibidos correctamente</b>\n\n"
                    f"📱 <b>Desde:</b> Mini App\n"
                    f"👤 <b>Usuario:</b> {user.name}\n"
                    f"📊 <b>Datos:</b>\n"
                    f"<pre><code>{json.dumps(data, indent=2, ensure_ascii=False)}</code></pre>\n\n"
                    f"¿Qué deseas hacer ahora?"
                )
                keyboard = TelegramWebhookManagerService._create_main_menu_keyboard()
                TelegramWebhookManagerService._send_message_to_telegram(chat_id, success_message, keyboard)
                
        except json.JSONDecodeError:
            error_message = (
                f"❌ <b>Error al procesar datos</b>\n\n"
                f"Los datos recibidos no tienen un formato válido.\n"
                f"Por favor, intenta de nuevo."
            )
            TelegramWebhookManagerService._send_message_to_telegram(chat_id, error_message)
        except Exception as e:
            logger.error(f"Error procesando datos de webapp: {e}")
            error_message = (
                f"❌ <b>Error interno</b>\n\n"
                f"Ocurrió un error procesando tu solicitud.\n"
                f"Por favor, intenta de nuevo más tarde."
            )
            TelegramWebhookManagerService._send_message_to_telegram(chat_id, error_message)
    
    @staticmethod
    def _handle_registration_data(chat_id: int, data: dict, user: TelegramUserSchema):
        """Maneja datos específicos de registro de usuario desde la Mini Web App"""
        try:
            name = data.get('name', '').strip()
            age = int(data.get('age', 0))
            
            # Validar datos
            if not name or len(name) < 2:
                error_message = (
                    f"❌ <b>Error en el registro</b>\n\n"
                    f"El nombre debe tener al menos 2 caracteres.\n"
                    f"Por favor, intenta de nuevo."
                )
                keyboard = TelegramWebhookManagerService._create_registration_keyboard()
                TelegramWebhookManagerService._send_message_with_keyboard(chat_id, error_message, keyboard)
                return
            
            if age < 13 or age > 120:
                error_message = (
                    f"❌ <b>Error en el registro</b>\n\n"
                    f"La edad debe estar entre 13 y 120 años.\n"
                    f"Por favor, intenta de nuevo."
                )
                keyboard = TelegramWebhookManagerService._create_registration_keyboard()
                TelegramWebhookManagerService._send_message_with_keyboard(chat_id, error_message, keyboard)
                return
            
            # Completar registro
            user.name = name
            user.age = age
            user.registration_state = UserRegistrationState.COMPLETED
            user.registered_at = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            TelegramWebhookManagerService._save_user(user)
            
            # Mensaje de éxito simplificado
            success_message = (
                f"✅ <b>¡Registro exitoso!</b>\n\n"
                f"Bienvenido <b>{user.name}</b> a GymBot\n\n"
                f"<b>Datos registrados:</b>\n"
                f"• Nombre: {user.name}\n"
                f"• Edad: {user.age} años\n"
                f"• Fecha: {user.registered_at.strftime('%d/%m/%Y %H:%M')}"
            )
            keyboard = TelegramWebhookManagerService._create_main_menu_keyboard()
            TelegramWebhookManagerService._send_message_with_keyboard(chat_id, success_message, keyboard)
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error procesando datos de registro: {e}")
            error_message = (
                f"❌ <b>Error en el registro</b>\n\n"
                f"Los datos recibidos no son válidos.\n"
                f"Por favor, intenta de nuevo."
            )
            keyboard = TelegramWebhookManagerService._create_registration_keyboard()
            TelegramWebhookManagerService._send_message_with_keyboard(chat_id, error_message, keyboard)

    @staticmethod
    def _handle_rutina_completa_data(chat_id: int, data: dict, user: TelegramUserSchema):
        """Maneja datos específicos de rutina completa"""
        rutina = data.get('rutina', {})
        ejercicios = rutina.get('ejercicios', [])
        
        message = (
            f"🏋️ <b>Rutina Registrada Exitosamente</b>\n\n"
            f"👤 <b>Usuario:</b> {user.name}\n"
            f"📝 <b>Nombre:</b> {rutina.get('nombre', 'Sin nombre')}\n"
            f"⏱️ <b>Duración:</b> {rutina.get('duracion', 'No especificada')}\n"
            f"🎯 <b>Objetivo:</b> {rutina.get('objetivo', 'General')}\n\n"
            f"💪 <b>Ejercicios ({len(ejercicios)}):</b>\n"
        )
        
        for i, ejercicio in enumerate(ejercicios[:5], 1):  # Mostrar máximo 5
            message += f"{i}. {ejercicio.get('nombre', 'Sin nombre')} - {ejercicio.get('series', '?')}x{ejercicio.get('repeticiones', '?')}\n"
        
        if len(ejercicios) > 5:
            message += f"... y {len(ejercicios) - 5} ejercicios más\n"
        
        message += f"\n✅ <b>¡Rutina guardada correctamente!</b>"
        
        keyboard = TelegramWebhookManagerService._create_main_menu_keyboard()
        TelegramWebhookManagerService._send_message_to_telegram(chat_id, message, keyboard)
    
    @staticmethod
    def _handle_perfil_avanzado_data(chat_id: int, data: dict, user: TelegramUserSchema):
        """Maneja datos específicos de perfil avanzado"""
        perfil = data.get('perfil', {})
        
        # Actualizar datos del usuario si se proporcionaron
        if perfil.get('nombre'):
            user.name = perfil['nombre']
        if perfil.get('edad'):
            user.age = perfil['edad']
        
        user.updated_at = datetime.utcnow()
        TelegramWebhookManagerService._save_user(user)
        
        message = (
            f"👤 <b>Perfil Actualizado</b>\n\n"
            f"✅ <b>Información guardada:</b>\n"
            f"📝 <b>Nombre:</b> {user.name}\n"
            f"🎂 <b>Edad:</b> {user.age} años\n"
        )
        
        if perfil.get('peso'):
            message += f"⚖️ <b>Peso:</b> {perfil['peso']} kg\n"
        if perfil.get('altura'):
            message += f"📏 <b>Altura:</b> {perfil['altura']} cm\n"
        if perfil.get('objetivo_fitness'):
            message += f"🎯 <b>Objetivo:</b> {perfil['objetivo_fitness']}\n"
        
        message += f"\n🎉 <b>¡Perfil actualizado correctamente!</b>"
        
        keyboard = TelegramWebhookManagerService._create_main_menu_keyboard()
        TelegramWebhookManagerService._send_message_to_telegram(chat_id, message, keyboard)
    
    @staticmethod
    def _handle_dashboard_data(chat_id: int, data: dict, user: TelegramUserSchema):
        """Maneja datos específicos del dashboard"""
        action = data.get('action', 'view')
        
        if action == 'export_data':
            message = (
                f"📊 <b>Exportación de Datos</b>\n\n"
                f"👤 <b>Usuario:</b> {user.name}\n"
                f"📅 <b>Fecha:</b> {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}\n\n"
                f"📈 <b>Resumen de actividad:</b>\n"
                f"• Rutinas completadas: 0\n"
                f"• Días activos: 0\n"
                f"• Tiempo total: 0 min\n\n"
                f"💾 <b>Datos exportados correctamente</b>"
            )
        else:
            message = (
                f"📊 <b>Dashboard Actualizado</b>\n\n"
                f"✅ <b>Acción procesada:</b> {action}\n"
                f"👤 <b>Usuario:</b> {user.name}\n\n"
                f"🎯 <b>¡Información actualizada!</b>"
            )
        
        keyboard = TelegramWebhookManagerService._create_main_menu_keyboard()
        TelegramWebhookManagerService._send_message_to_telegram(chat_id, message, keyboard)

    @staticmethod
    def _show_today_workout(chat_id: int, user: TelegramUserSchema):
        """Muestra el entrenamiento programado para hoy"""
        # Simular datos de localStorage (en producción esto vendría de base de datos)
        today = datetime.utcnow().strftime('%d/%m/%Y')
        
        message = (
            f"📅 <b>Entrenamiento de Hoy</b>\n\n"
            f"<b>Fecha:</b> {today}\n\n"
            f"🏋️ <b>Ejercicios programados:</b>\n"
            f"• Press banca - 3x8-12\n"
            f"• Sentadillas - 3x10-15\n"
            f"• Dominadas - 3x5-8\n"
            f"• Flexiones - 2x max\n\n"
            f"💡 Escribe <b>entrenar</b> para registrar tu sesión"
        )
        
        keyboard = TelegramWebhookManagerService._create_main_menu_keyboard()
        TelegramWebhookManagerService._send_message_to_telegram(chat_id, message, keyboard)

    @staticmethod
    def _show_training_session(chat_id: int, user: TelegramUserSchema):
        """Muestra la sesión de entrenamiento interactiva"""
        message = (
            f"🏋️ <b>Sesión de Entrenamiento</b>\n\n"
            f"<b>Hola {user.name}!</b> Registra tu entrenamiento:\n\n"
            f"📝 <b>Formato:</b>\n"
            f"Ejercicio - Series x Repeticiones @ Peso\n\n"
            f"<b>Ejemplo:</b>\n"
            f"Press banca - 3x10 @ 60kg\n"
            f"Sentadillas - 3x12 @ 80kg\n\n"
            f"💪 Envía tu entrenamiento en ese formato"
        )
        
        keyboard = TelegramWebhookManagerService._create_main_menu_keyboard()
        TelegramWebhookManagerService._send_message_to_telegram(chat_id, message, keyboard)

    @staticmethod
    def _handle_delete_account(chat_id: int, data: dict, user: TelegramUserSchema):
        """Maneja la eliminación de cuenta desde settings webapp"""
        if data.get('confirmed'):
            # Eliminar usuario
            if chat_id in users_db:
                del users_db[chat_id]
                logger.info(f"Cuenta eliminada para chat_id={chat_id}")
            
            message = (
                f"✅ <b>Cuenta eliminada</b>\n\n"
                f"Tu cuenta ha sido eliminada exitosamente.\n"
                f"Esperamos verte de nuevo pronto."
            )
            TelegramWebhookManagerService._send_message_to_telegram(chat_id, message)
        else:
            message = (
                f"❌ <b>Eliminación cancelada</b>\n\n"
                f"Tu cuenta no ha sido eliminada."
            )
            keyboard = TelegramWebhookManagerService._create_main_menu_keyboard()
            TelegramWebhookManagerService._send_message_with_keyboard(chat_id, message, keyboard)
    
    @staticmethod
    def _handle_profile_update(chat_id: int, data: dict, user: TelegramUserSchema):
        """Maneja la actualización del perfil desde settings webapp"""
        try:
            name = data.get('name', '').strip()
            age = int(data.get('age', 0))
            
            # Validar datos
            if not name or len(name) < 2:
                error_message = (
                    f"❌ <b>Error actualizando perfil</b>\n\n"
                    f"El nombre debe tener al menos 2 caracteres."
                )
                TelegramWebhookManagerService._send_message_to_telegram(chat_id, error_message)
                return
            
            if age < 13 or age > 120:
                error_message = (
                    f"❌ <b>Error actualizando perfil</b>\n\n"
                    f"La edad debe estar entre 13 y 120 años."
                )
                TelegramWebhookManagerService._send_message_to_telegram(chat_id, error_message)
                return
            
            # Actualizar perfil
            old_name = user.name
            old_age = user.age
            user.name = name
            user.age = age
            user.updated_at = datetime.utcnow()
            TelegramWebhookManagerService._save_user(user)
            
            # Mensaje de confirmación
            success_message = (
                f"✅ <b>Perfil actualizado</b>\n\n"
                f"📝 <b>Nombre:</b> {old_name} → {user.name}\n"
                f"🎂 <b>Edad:</b> {old_age} → {user.age} años\n\n"
                f"✨ <b>¡Cambios guardados exitosamente!</b>"
            )
            keyboard = TelegramWebhookManagerService._create_main_menu_keyboard()
            TelegramWebhookManagerService._send_message_with_keyboard(chat_id, success_message, keyboard)
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error actualizando perfil: {e}")
            error_message = (
                f"❌ <b>Error actualizando perfil</b>\n\n"
                f"Los datos recibidos no son válidos."
            )
            TelegramWebhookManagerService._send_message_to_telegram(chat_id, error_message)