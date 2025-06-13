import secrets


# TELEGRAM requiere un token de 32–256 caracteres
secret_token = secrets.token_urlsafe(192)
print(secret_token)