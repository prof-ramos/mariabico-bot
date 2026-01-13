"""Validadores para inputs do bot."""
import html
import re
from urllib.parse import urlparse


# Padrão de URL Shopee válido
SHOPEE_URL_PATTERN = re.compile(
    r"^(https?://)?(www\.)?(shopee\.com\.br|shope\.ee)/",
    re.IGNORECASE
)


def is_valid_shopee_url(url: str) -> bool:
    """Valida se a URL é do Shopee.

    Args:
        url: URL para validar

    Returns:
        True se URL é válida
    """
    if not url or not isinstance(url, str):
        return False

    # Remove espaços antes de validar
    url = url.strip()

    if len(url) > 2048:
        return False

    return bool(SHOPEE_URL_PATTERN.match(url))


def normalize_shopee_url(url: str) -> str:
    """Normaliza URL Shopee para formato padrão.

    Args:
        url: URL para normalizar

    Returns:
        URL normalizada

    Raises:
        TypeError: Se url não for string
        ValueError: Se url for vazia ou apenas espaços
    """
    if not isinstance(url, str):
        raise TypeError(f"url deve ser uma string, recebido: {type(url).__name__}")

    # Remove espaços
    url = url.strip()

    if not url:
        raise ValueError("url não pode ser vazia")

    # Adiciona https se não tiver protocolo
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Remove parâmetros de rastreamento desnecessários
    parsed = urlparse(url)
    cleaned = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    return cleaned


def escape_html(text: str) -> str:
    """Escapa caracteres especiais HTML.

    Usa html.escape da stdlib para garantir corretude.

    Args:
        text: Texto para escapar

    Returns:
        Texto com HTML escapado
    """
    # html.escape escapa <, >, &, e " com quote=True
    escaped = html.escape(text, quote=True)

    # Adicionalmente escapa aspas simples para contextos que requerem
    escaped = escaped.replace("'", "&#x27;")

    return escaped
