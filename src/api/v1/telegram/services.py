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
        """Crea el teclado principal con las opciones del menú"""
        return {
            "inline_keyboard": [
                [{"text": "📝 Registrar Rutina", "callback_data": "register_routine"}],
                [{"text": "✏️ Editar Rutina", "callback_data": "edit_routine"}],
                [{"text": "👀 Ver Rutina", "callback_data": "view_routine"}],
                [{"text": "👤 Mi Perfil", "callback_data": "my_profile"}],
                [{"text": "⚙️ Editar Datos", "callback_data": "edit_profile"}]
            ]
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
    def _handle_not_registered_user(chat_id: int, text: str, from_user: dict):
        """Maneja usuarios no registrados"""
        if text and text.lower() == "/registrar":
            # Crear usuario en estado de espera del nombre
            user = TelegramUserSchema(
                chat_id=chat_id,
                user_id=from_user.get("id"),
                username=from_user.get("username"),
                first_name=from_user.get("first_name"),
                last_name=from_user.get("last_name"),
                registration_state=UserRegistrationState.WAITING_NAME,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            TelegramWebhookManagerService._save_user(user)
            
            # Enviar mensaje pidiendo el nombre con diseño mejorado
            message = (
                f"╭─────────────────────────╮\n"
                f"│  <b>🎉 ¡GENIAL! 🎉</b>  │\n"
                f"╰─────────────────────────╯\n\n"
                f"✨ <b>Vamos a registrarte en</b>\n"
                f"<b>nuestra aplicación</b> ✨\n\n"
                f"┌─────────────────────────┐\n"
                f"│ 📝 Para comenzar, compárteme │\n"
                f"│    tu <b>nombre completo:</b>     │\n"
                f"└─────────────────────────┘"
            )
            TelegramWebhookManagerService._send_message_to_telegram(chat_id, message)
        else:
            # Usuario no registrado, pedirle que se registre
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
    
    @staticmethod
    def _handle_waiting_name(chat_id: int, text: str, user: TelegramUserSchema):
        """Maneja el estado de espera del nombre"""
        if not text or len(text.strip()) < 2:
            message = "Por favor, ingresa un nombre válido (mínimo 2 caracteres):"
            TelegramWebhookManagerService._send_message_to_telegram(chat_id, message)
            return
        
        # Guardar nombre y cambiar estado
        user.name = text.strip()
        user.registration_state = UserRegistrationState.WAITING_AGE
        user.updated_at = datetime.utcnow()
        TelegramWebhookManagerService._save_user(user)
        
        # Pedir edad
        message = (
            f"¡Perfecto, {user.name}! 😊\n\n"
            "Ahora necesito que me compartas tu <b>edad</b> (solo números):"
        )
        TelegramWebhookManagerService._send_message_to_telegram(chat_id, message)
    
    @staticmethod
    def _handle_waiting_age(chat_id: int, text: str, user: TelegramUserSchema):
        """Maneja el estado de espera de la edad"""
        try:
            age = int(text.strip())
            if age < 13 or age > 120:
                message = "Por favor, ingresa una edad válida (entre 13 y 120 años):"
                TelegramWebhookManagerService._send_message_to_telegram(chat_id, message)
                return
            
            # Completar registro
            user.age = age
            user.registration_state = UserRegistrationState.COMPLETED
            user.registered_at = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            TelegramWebhookManagerService._save_user(user)
            
            # Mensaje de bienvenida completo con diseño mejorado
            welcome_message = (
                f"╭─────────────────────────╮\n"
                f"│ <b>🎉 ¡REGISTRO EXITOSO! 🎉</b> │\n"
                f"╰─────────────────────────╯\n\n"
                f"✅ <b>¡Excelente, {user.name}!</b>\n\n"
                f"🎊 <b>Tu registro se completó</b>\n"
                f"<b>exitosamente</b> 🎊\n\n"
                f"🔓 <b>Ahora tienes acceso completo</b>\n"
                f"<b>a todas las funciones del bot</b>\n\n"
                f"┌─────────────────────────┐\n"
                f"│   💪 <b>¿Listo para empezar</b>   │\n"
                f"│    <b>tu rutina perfecta?</b>    │\n"
                f"└─────────────────────────┘"
            )
            keyboard = TelegramWebhookManagerService._create_main_menu_keyboard()
            TelegramWebhookManagerService._send_message_to_telegram(chat_id, welcome_message, keyboard)
            
        except ValueError:
            message = "Por favor, ingresa solo números para tu edad:"
            TelegramWebhookManagerService._send_message_to_telegram(chat_id, message)
    
    @staticmethod
    def _handle_registered_user(chat_id: int, text: str, user: TelegramUserSchema):
        """Maneja usuarios ya registrados"""
        # Comandos especiales
        if text.lower() in ["/miperfil", "/perfil", "/datos"]:
            TelegramWebhookManagerService._show_user_profile(chat_id, user)
            return
        elif text.lower() in ["/editarnombre", "/editaredad", "/editardatos"]:
            TelegramWebhookManagerService._show_edit_options(chat_id, user)
            return
        
        # Mensaje de bienvenida normal con diseño mejorado
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
    
    @staticmethod
    def _show_user_profile(chat_id: int, user: TelegramUserSchema):
        """Muestra el perfil del usuario"""
        registered_date = user.registered_at.strftime("%d/%m/%Y a las %H:%M") if user.registered_at else "No disponible"
        
        # Diseño mejorado con marcos decorativos y mejor formato
        profile_message = (
            f"╭─────────────────────────╮\n"
            f"│    <b>✨ TU PERFIL ✨</b>    │\n"
            f"╰─────────────────────────╯\n\n"
            f"🏷️ <b>Nombre:</b>\n"
            f"    <i>{user.name}</i>\n\n"
            f"🎂 <b>Edad:</b>\n"
            f"    <i>{user.age} años</i>\n\n"
            f"📅 <b>Miembro desde:</b>\n"
            f"    <i>{registered_date}</i>\n\n"
            f"🆔 <b>ID del Chat:</b>\n"
            f"    <code>{user.chat_id}</code>\n\n"
            f"┌─────────────────────────┐\n"
            f"│ 💡 <i>Tip: Usa /editardatos para</i>  │\n"
            f"│    <i>actualizar tu información</i>    │\n"
            f"└─────────────────────────┘"
        )
        
        keyboard = TelegramWebhookManagerService._create_main_menu_keyboard()
        TelegramWebhookManagerService._send_message_to_telegram(chat_id, profile_message, keyboard)
    
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