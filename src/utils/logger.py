"""Logging estruturado em JSON para o MariaBicoBot."""
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

# Componentes do sistema
COMPONENTS = [
    "bot",
    "curator",
    "link_gen",
    "deduplicator",
    "shopee_client",
    "database",
    "scheduler",
]


class JSONFormatter(logging.Formatter):
    """Formatter que outputa logs em JSON estruturado."""

    def format(self, record: logging.LogRecord) -> str:
        """Formata o log record como JSON."""
        # Usa UTC para timestamp consistente
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "component": getattr(record, "component", "unknown"),
            "message": record.getMessage(),
        }

        # Adiciona contexto se disponível
        if hasattr(record, "context"):
            log_data["context"] = record.context

        # Adiciona exceção se houver
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(
    name: str = "mariabicobot",
    level: str = "INFO",
    component: str = "unknown",
) -> logging.LoggerAdapter:
    """Configura um logger com output JSON estruturado.

    Args:
        name: Nome do logger
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        component: Componente do sistema

    Returns:
        LoggerAdapter configurado
    """
    logger = logging.getLogger(name)

    # Evita adicionar handlers duplicados
    if logger.handlers:
        return logging.LoggerAdapter(logger, {"component": component})

    # Configura nível
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Handler para stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(JSONFormatter())

    logger.addHandler(handler)

    # Adapter para adicionar component automaticamente
    return logging.LoggerAdapter(logger, {"component": component})


def get_logger(name: str, component: str, level: int = logging.INFO) -> logging.LoggerAdapter:
    """Retorna um logger para um componente específico.

    Args:
        name: Nome do logger
        component: Componente do sistema
        level: Nível de log (opcional)

    Returns:
        LoggerAdapter com component pré-configurado
    """
    return setup_logger(name, component=component, level=level)


class LogContext:
    """Context manager para adicionar contexto aos logs."""

    def __init__(self, logger: logging.LoggerAdapter, **context):
        self.logger = logger
        self.context = context
        self.old_context = {}

    def __enter__(self):
        if hasattr(self.logger, "extra"):
            self.old_context = self.logger.extra.copy()
            self.logger.extra.update(self.context)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self.logger, "extra"):
            self.logger.extra = self.old_context
