"""Configurações e variáveis de ambiente do MariaBicoBot."""
import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Configurações da aplicação."""

    # Telegram
    telegram_bot_token: str
    admin_telegram_user_id: int
    target_group_id: int

    # Shopee
    shopee_app_id: str
    shopee_secret: str

    # Geral
    tz: str
    log_level: str
    db_path: str

    # Scheduler
    schedule_cron: str

    @classmethod
    def from_env(cls) -> "Settings":
        """Carrega configurações das variáveis de ambiente."""
        telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN é obrigatório")

        admin_user_id = os.getenv("ADMIN_TELEGRAM_USER_ID")
        if not admin_user_id:
            raise ValueError("ADMIN_TELEGRAM_USER_ID é obrigatório")

        target_group_id = os.getenv("TARGET_GROUP_ID")
        if not target_group_id:
            raise ValueError("TARGET_GROUP_ID é obrigatório")

        shopee_app_id = os.getenv("SHOPEE_APP_ID")
        if not shopee_app_id:
            raise ValueError("SHOPEE_APP_ID é obrigatório")

        shopee_secret = os.getenv("SHOPEE_SECRET")
        if not shopee_secret:
            raise ValueError("SHOPEE_SECRET é obrigatório")

        # Converte para int com tratamento de erro
        try:
            admin_user_id_int = int(admin_user_id)
        except ValueError:
            raise ValueError(f"ADMIN_TELEGRAM_USER_ID deve ser um número inteiro válido: '{admin_user_id}'")

        try:
            target_group_id_int = int(target_group_id)
        except ValueError:
            raise ValueError(f"TARGET_GROUP_ID deve ser um número inteiro válido: '{target_group_id}'")

        return cls(
            telegram_bot_token=telegram_bot_token,
            admin_telegram_user_id=admin_user_id_int,
            target_group_id=target_group_id_int,
            shopee_app_id=shopee_app_id,
            shopee_secret=shopee_secret,
            tz=os.getenv("TZ", "America/Sao_Paulo"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            db_path=os.getenv("DB_PATH", "/data/mariabico.db"),
            schedule_cron=os.getenv("SCHEDULE_CRON", "0 */12 * * *"),
        )

    def validate(self) -> None:
        """Valida as configurações."""
        # Valida token Telegram: formato {bot_id}:{secret}
        if ":" not in self.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN inválido: deve estar no formato {bot_id}:{secret}")

        parts = self.telegram_bot_token.split(":")
        if len(parts) != 2:
            raise ValueError("TELEGRAM_BOT_TOKEN inválido: deve ter exatamente um separador ':'")

        bot_id, secret = parts
        if not bot_id.isdigit():
            raise ValueError("TELEGRAM_BOT_TOKEN inválido: bot_id deve ser numérico")
        if len(secret) < 20:
            raise ValueError("TELEGRAM_BOT_TOKEN inválido: secret muito curto (mínimo 20 caracteres)")

        if self.admin_telegram_user_id <= 0:
            raise ValueError("ADMIN_TELEGRAM_USER_ID deve ser positivo")

        if self.target_group_id >= 0:
            raise ValueError("TARGET_GROUP_ID deve ser negativo (grupo)")

        if not self.shopee_app_id.isdigit():
            raise ValueError("SHOPEE_APP_ID deve ser numérico")

        if len(self.shopee_secret) < 32:
            raise ValueError("SHOPEE_SECRET muito curto")


# Instância global de configurações
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Retorna a instância de configurações (singleton)."""
    global settings
    if settings is None:
        settings = Settings.from_env()
        settings.validate()
    return settings


def reload_settings() -> Settings:
    """Recarrega as configurações (útil para testes)."""
    global settings
    settings = Settings.from_env()
    settings.validate()
    return settings
