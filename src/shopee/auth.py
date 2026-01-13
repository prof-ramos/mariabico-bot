"""Autenticação SHA256 para Shopee Affiliate API."""
import hashlib
import time


def generate_signature(app_id: str, secret: str, timestamp: int, payload: str) -> str:
    """Gera assinatura SHA256 para Shopee API.

    Nota: A Shopee usa SHA256 simples, não HMAC-SHA256.
    Fórmula: SHA256(app_id + timestamp + payload + secret)

    Args:
        app_id: App ID da Shopee
        secret: Secret key da Shopee
        timestamp: Timestamp Unix em segundos
        payload: Corpo da requisição (query GraphQL)

    Returns:
        Assinatura SHA256 hexadecimal

    Raises:
        ValueError: Se algum parâmetro for inválido
    """
    # Validação de inputs
    if not app_id or not isinstance(app_id, str):
        raise ValueError("app_id deve ser uma string não vazia")
    if not secret or not isinstance(secret, str):
        raise ValueError("secret deve ser uma string não vazia")
    if not payload or not isinstance(payload, str):
        raise ValueError("payload deve ser uma string não vazia")
    if not isinstance(timestamp, int) or timestamp < 0:
        raise ValueError("timestamp deve ser um inteiro não negativo")

    message = f"{app_id}{timestamp}{payload}{secret}"
    return hashlib.sha256(message.encode()).hexdigest()


def get_auth_headers(app_id: str, secret: str, payload: str) -> dict:
    """Retorna headers de autenticação para requisição Shopee.

    Args:
        app_id: App ID da Shopee
        secret: Secret key da Shopee
        payload: Corpo da requisição (query GraphQL)

    Returns:
        Dicionário com headers de autenticação
    """
    timestamp = int(time.time())
    signature = generate_signature(app_id, secret, timestamp, payload)

    return {
        "Authorization": f"SHA256 Credential={app_id}, Timestamp={timestamp}, Signature={signature}",
        "Content-Type": "application/json",
    }
