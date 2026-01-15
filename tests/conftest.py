"""Configuração centralizada do pytest com orquestração inteligente."""

import asyncio
import os
import sqlite3

# Adiciona src ao path
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# CONFIGURAÇÃO DE PARALELIZAÇÃO E ORQUESTRAÇÃO
# ============================================================================


def pytest_configure(config):
    """Configura hooks personalizados do pytest."""
    config.addinivalue_line(
        "markers", "unit: Testes unitários (rápidos, isolados, sem dependências externas)"
    )
    config.addinivalue_line(
        "markers", "integration: Testes de integração (requer recursos externos)"
    )
    config.addinivalue_line("markers", "slow: Testes lentos (devem ser executados separadamente)")
    config.addinivalue_line("markers", "shopee_api: Testes que chamam API Shopee real")
    config.addinivalue_line("markers", "telegram: Testes relacionados ao Telegram")
    config.addinivalue_line("markers", "database: Testes que acessam banco de dados")
    config.addinivalue_line("markers", "smoke: Testes críticos de smoke (executam primeiro)")


@pytest.fixture(scope="session")
def event_loop_policy() -> Any:
    """Configura policy de event loop para testes assíncronos."""
    policy = asyncio.get_event_loop_policy()
    policy.get_event_loop = asyncio.new_event_loop
    return policy


# ============================================================================
# FIXTURES DE BANCO DE DADOS
# ============================================================================


@pytest.fixture(scope="function")
def temp_db_path() -> Generator[str, None, None]:
    """Cria um banco SQLite temporário para testes."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        # Inicializa schema
        from src.database import init_db

        init_db(path)
        yield path
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


@pytest.fixture(scope="function")
def db(temp_db_path: str) -> Generator[Any, None, None]:
    """Fixture de banco de dados para testes."""
    from src.database import Database

    database = Database(temp_db_path)
    yield database
    database.close()


@pytest.fixture(scope="function")
def db_conn(temp_db_path: str) -> Generator[sqlite3.Connection, None, None]:
    """Conexão bruta SQLite para testes de baixo nível."""
    conn = sqlite3.connect(temp_db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ============================================================================
# FIXTURES PARA SHEPEE API (MOCK)
# ============================================================================


@pytest.fixture(scope="function")
def mock_shopee_response() -> dict:
    """Resposta padrão mockada da API Shopee."""
    return {
        "data": {
            "productOfferV2": {
                "nodes": [
                    {
                        "itemId": 123456789,
                        "productName": "Fone Bluetooth Premium",
                        "priceMin": "89.90",
                        "priceMax": "89.90",
                        "priceDiscountRate": 30,
                        "commissionRate": "0.10",
                        "commission": "8.99",
                        "sales": 1500,
                        "ratingStar": "4.8",
                        "imageUrl": "https://cf.shopee.com.br/file/test.jpg",
                        "shopId": 1404215442,
                        "shopName": "Loja Teste",
                        "shopType": [1],
                        "productLink": "https://shopee.com.br/product/test",
                        "offerLink": "https://shope.ee/test123",
                        "periodStartTime": 1764558000,
                        "periodEndTime": 32503651199,
                    }
                ],
                "pageInfo": {"page": 1, "limit": 50, "hasNextPage": False},
            }
        }
    }


@pytest.fixture(scope="function")
def mock_shopee_client():
    """Cliente Shopee mockado."""
    from src.shopee import ShopeeClient

    with patch.object(ShopeeClient, "__init__", lambda self, app_id, secret: None):
        client = ShopeeClient("test_app", "test_secret")
        client.app_id = "test_app"
        client.secret = "test_secret"

    # Mock dos métodos assíncronos
    client.search_products = AsyncMock(return_value=[])
    client.generate_short_link = AsyncMock(return_value="https://shope.ee/mock123")
    client.close = AsyncMock()

    return client


@pytest.fixture(scope="function")
def mock_shopee_response_product() -> dict:
    """Produto mockado da API Shopee (formato productOfferV2)."""
    return {
        "itemId": 123456789,
        "productName": "Fone Bluetooth Teste",
        "priceMin": "99.90",
        "priceMax": "99.90",
        "priceDiscountRate": 25,
        "commissionRate": "0.10",
        "commission": "9.99",
        "sales": 500,
        "ratingStar": "4.7",
        "imageUrl": "https://cf.shopee.com.br/file/test.jpg",
        "shopId": 123456,
        "shopName": "Loja Teste",
        "shopType": [1],
        "productLink": "https://shopee.com.br/product/test",
        "offerLink": "https://shope.ee/test",
    }


# ============================================================================
# FIXTURES PARA CONFIGURAÇÃO
# ============================================================================


@pytest.fixture(scope="function", autouse=True)
def mock_settings():
    """Settings mockados para testes."""
    from src.config import Settings

    with patch.dict(
        os.environ,
        {
            "TELEGRAM_BOT_TOKEN": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123456",
            "ADMIN_TELEGRAM_USER_ID": "123456789",
            "TARGET_GROUP_ID": "-1001234567890",
            "SHOPEE_APP_ID": "123456",
            "SHOPEE_SECRET": "abcdef1234567890abcdef1234567890",
            "TZ": "America/Sao_Paulo",
            "LOG_LEVEL": "DEBUG",
            "DB_PATH": ":memory:",
            "SCHEDULE_CRON": "0 */12 * * *",
        },
        clear=True,
    ):
        new_settings = Settings.from_env()

        with patch("src.config.settings", new_settings):
            yield new_settings


@pytest.fixture(scope="function")
def reset_settings():
    """Reseta settings singleton entre testes."""
    from src import config

    original_settings = config.settings
    config.settings = None
    yield
    config.settings = original_settings


# ============================================================================
# FIXTURES PARA CURATOR
# ============================================================================


@pytest.fixture(scope="function")
def curator(mock_shopee_client, db, reset_settings):
    """Instância de Curator para testes."""
    from src.core import Curator

    return Curator(
        shopee_client=mock_shopee_client,
        db=db,
        group_id="-1001234567890",
        group_hash="test",
        top_n=10,
        max_pages=2,
        page_limit=25,
        dedup_days=7,
    )


# ============================================================================
# FIXTURES PARA PRODUTOS
# ============================================================================


@pytest.fixture(scope="function")
def sample_product() -> dict:
    """Produto de exemplo para testes."""
    return {
        "itemId": "123456789",
        "productName": "Fone Bluetooth Teste",
        "priceMin": 99.90,
        "priceDiscountRate": 25,
        "commissionRate": 0.10,
        "commission": 9.99,
        "originUrl": "https://shopee.com.br/product/test",
        "imageUrl": "https://cf.shopee.com.br/file/test.jpg",
        "rating": 4.7,
        "keyword": "fone",
    }


@pytest.fixture(scope="function")
def sample_products() -> list[dict]:
    """Lista de produtos de exemplo para testes."""
    return [
        {
            "itemId": str(i),
            "productName": f"Produto {i}",
            "priceMin": 50.0 + i * 10,
            "priceDiscountRate": 10 + i * 5,
            "commissionRate": 0.08 + i * 0.01,
            "commission": (50.0 + i * 10) * (0.08 + i * 0.01),
            "originUrl": f"https://shopee.com.br/product/{i}",
            "imageUrl": f"https://cf.shopee.com.br/file/{i}.jpg",
            "rating": 4.5,
            "keyword": "teste",
        }
        for i in range(1, 6)
    ]


# ============================================================================
# FIXTURES PARA TELEGRAM (MOCK)
# ============================================================================


@pytest.fixture(scope="function")
def mock_telegram_update():
    """Update do Telegram mockado."""
    from telegram import Update, User

    user = MagicMock(spec=User)
    user.id = 123456789
    user.is_bot = False
    user.first_name = "Test User"

    # Mock Update object completely
    update = MagicMock(spec=Update)
    update.update_id = 1
    update.effective_user = user

    # Mock callback query
    callback_query = MagicMock()
    callback_query.data = "menu"
    callback_query.from_user = user
    callback_query.answer = AsyncMock()
    callback_query.edit_message_text = AsyncMock()

    update.callback_query = callback_query
    # Default message to None (callback case)
    update.message = None

    return update


@pytest.fixture(scope="function")
def mock_telegram_context(mock_shopee_client, db, curator):
    """Contexto do Telegram mockado."""

    context = MagicMock()
    context.bot_data = {
        "db": db,
        "shopee": mock_shopee_client,
        "curator": curator,
    }
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()

    return context


# ============================================================================
# ORQUESTRAÇÃO DE TESTES - MARCADORES E FILTROS
# ============================================================================


class TestClassifier:
    """Classifica e organiza testes para execução otimizada."""

    @staticmethod
    def is_fast_test(item: pytest.Item) -> bool:
        """Identifica testes rápidos (unitários)."""
        return any(m.name == "unit" for m in item.iter_markers())

    @staticmethod
    def is_slow_test(item: pytest.Item) -> bool:
        """Identifica testes lentos."""
        return any(m.name in ("slow", "integration") for m in item.iter_markers())

    @staticmethod
    def is_smoke_test(item: pytest.Item) -> bool:
        """Identifica testes de smoke críticos."""
        return any(m.name == "smoke" for m in item.iter_markers())

    @staticmethod
    def requires_external_api(item: pytest.Item) -> bool:
        """Identifica testes que requerem APIs externas."""
        return any(m.name in ("shopee_api", "telegram") for m in item.iter_markers())


def pytest_collection_modifyitems(config, items):
    """Modifica a coleção de testes para otimizar execução."""

    # Ordena por: smoke > unitários > lentos
    def sort_key(item):
        if TestClassifier.is_smoke_test(item):
            return 0
        if TestClassifier.is_fast_test(item):
            return 1
        if TestClassifier.is_slow_test(item):
            return 2
        return 3

    items.sort(key=sort_key)


# ============================================================================
# RELATÓRIOS PERSONALIZADOS
# ============================================================================


@pytest.fixture(autouse=True)
def print_test_duration(request):
    """Imprime duração de cada teste para análise de performance."""
    import time

    start = time.time()
    yield
    duration = time.time() - start
    if duration > 1.0:  # Apenas para testes > 1s
        print(f"\n⏱️  {request.node.name} levou {duration:.2f}s")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook para relatório de testes com categorização."""
    outcome = yield
    report = outcome.get_result()

    # Adiciona categorias ao report
    if report.when == "call":
        if TestClassifier.is_smoke_test(item):
            report.category = "smoke"
        elif TestClassifier.is_fast_test(item):
            report.category = "unit"
        elif TestClassifier.is_slow_test(item):
            report.category = "slow"
        else:
            report.category = "general"