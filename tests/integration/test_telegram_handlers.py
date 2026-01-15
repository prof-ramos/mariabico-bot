"""Testes de integração para handlers do bot Telegram."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram.ext import ConversationHandler

from src.bot.handlers import (
    AWAITING_LINK,
    convert_link_message,
    convert_link_start,
    convert_link_timeout,
    curate_now_callback,
    help_callback,
    is_authorized,
    menu_callback,
    menu_command,
    status_callback,
)


class TestAuthorization:
    """Testes para verificação de autorização."""

    @pytest.mark.smoke
    @pytest.mark.telegram
    @pytest.mark.asyncio
    async def test_is_authorized_admin(self, mock_settings):
        """Admin configurado está autorizado."""
        from src.config import reload_settings

        reload_settings()
        authorized = is_authorized(123456789)
        assert authorized is True

    @pytest.mark.telegram
    @pytest.mark.asyncio
    async def test_is_authorized_unauthorized(self, mock_settings):
        """Usuário diferente não está autorizado."""
        from src.config import reload_settings

        reload_settings()
        authorized = is_authorized(999999999)
        assert authorized is False


class TestMenuHandlers:
    """Testes para handlers de menu."""

    @pytest.mark.smoke
    @pytest.mark.telegram
    @pytest.mark.asyncio
    async def test_menu_command_authorized(self, mock_telegram_update, mock_telegram_context):
        """Comando /menu funciona para usuário autorizado."""
        # Configura update como message (não callback)
        mock_telegram_update.callback_query = None
        mock_telegram_update.message = MagicMock()
        mock_telegram_update.message.text = "/menu"
        mock_telegram_update.message.reply_text = AsyncMock()
        mock_telegram_update.effective_user.id = 123456789

        await menu_command(mock_telegram_update, mock_telegram_context)

        # Verifica se respondeu
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args
        assert "MariaBico" in call_args[0][0]

    @pytest.mark.telegram
    @pytest.mark.asyncio
    async def test_menu_command_unauthorized(self, mock_telegram_update, mock_telegram_context):
        """Comando /menu ignora usuário não autorizado."""
        mock_telegram_update.callback_query = None
        mock_telegram_update.message = MagicMock()
        mock_telegram_update.message.reply_text = AsyncMock()
        mock_telegram_update.effective_user.id = 999999999

        await menu_command(mock_telegram_update, mock_telegram_context)

        # Não deve responder
        mock_telegram_update.message.reply_text.assert_not_called()

    @pytest.mark.smoke
    @pytest.mark.telegram
    @pytest.mark.asyncio
    async def test_menu_callback(self, mock_telegram_update, mock_telegram_context):
        """Callback do menu exibe opções."""
        await menu_callback(mock_telegram_update, mock_telegram_context)

        # Verifica se editou a mensagem
        mock_telegram_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.telegram
    @pytest.mark.asyncio
    async def test_help_callback(self, mock_telegram_update, mock_telegram_context):
        """Callback de ajuda exibe instruções."""
        await help_callback(mock_telegram_update, mock_telegram_context)

        mock_telegram_update.callback_query.edit_message_text.assert_called_once()


class TestStatusCallback:
    """Testes para callback de status."""

    @pytest.mark.smoke
    @pytest.mark.telegram
    @pytest.mark.asyncio
    async def test_status_callback_with_db(self, mock_telegram_update, mock_telegram_context, db):
        """Exibe status com banco disponível."""
        # Adiciona run ao banco
        db.start_run("test")
        db.end_run(1, items_fetched=100, items_approved=50, items_sent=10, success=True)

        await status_callback(mock_telegram_update, mock_telegram_context)

        mock_telegram_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.telegram
    @pytest.mark.asyncio
    async def test_status_callback_no_db(self, mock_telegram_update, mock_telegram_context):
        """Exibe erro quando banco não disponível."""
        mock_telegram_context.bot_data = {}

        await status_callback(mock_telegram_update, mock_telegram_context)

        # Verifica mensagem de erro
        call_args = mock_telegram_update.callback_query.edit_message_text.call_args
        assert "não disponível" in call_args[0][0]


class TestCurateNowCallback:
    """Testes para callback de curadoria imediata."""

    @pytest.mark.smoke
    @pytest.mark.telegram
    @pytest.mark.asyncio
    async def test_curate_now_success(self, mock_telegram_update, mock_telegram_context):
        """Executa curadoria com sucesso."""
        # Mocka curadoria
        curator = mock_telegram_context.bot_data.get("curator")
        curator.curate = AsyncMock(
            return_value={
                "fetched": 10,
                "approved": 5,
                "final": 3,
                "products": [
                    {
                        "itemId": "1",
                        "shortLink": "https://shope.ee/test",
                    }
                ],
            }
        )

        await curate_now_callback(mock_telegram_update, mock_telegram_context)

        # Verifica mensagens enviadas
        mock_telegram_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.telegram
    @pytest.mark.asyncio
    async def test_curate_now_no_products(self, mock_telegram_update, mock_telegram_context):
        """Lida quando nenhum produto é aprovado."""
        curator = mock_telegram_context.bot_data.get("curator")
        curator.curate = AsyncMock(
            return_value={
                "fetched": 10,
                "approved": 0,
                "final": 0,
                "products": [],
            }
        )

        await curate_now_callback(mock_telegram_update, mock_telegram_context)

        call_args = mock_telegram_update.callback_query.edit_message_text.call_args
        assert "Nenhum produto" in call_args[0][0]

    @pytest.mark.telegram
    @pytest.mark.asyncio
    async def test_curate_now_error(self, mock_telegram_update, mock_telegram_context):
        """Lida com erro na curadoria."""
        curator = mock_telegram_context.bot_data.get("curator")
        curator.curate = AsyncMock(side_effect=Exception("API error"))

        await curate_now_callback(mock_telegram_update, mock_telegram_context)

        call_args = mock_telegram_update.callback_query.edit_message_text.call_args
        assert "Erro" in call_args[0][0]


class TestConvertLinkHandlers:
    """Testes para conversão de links."""

    @pytest.mark.smoke
    @pytest.mark.telegram
    @pytest.mark.asyncio
    async def test_convert_link_start(self, mock_telegram_update, mock_telegram_context):
        """Inicia conversação de conversão."""
        next_state = await convert_link_start(mock_telegram_update, mock_telegram_context)

        assert next_state == AWAITING_LINK
        mock_telegram_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.smoke
    @pytest.mark.telegram
    @pytest.mark.asyncio
    async def test_convert_link_valid(self, mock_telegram_update, mock_telegram_context):
        """Converte link válido."""
        # Configura como message (não callback)
        mock_telegram_update.callback_query = None
        mock_telegram_update.message = MagicMock()
        mock_telegram_update.message.text = "https://shopee.com.br/product/test"
        mock_telegram_update.message.reply_text = AsyncMock()
        mock_telegram_update.effective_user.id = 123456789

        # Mocka API
        shopee = mock_telegram_context.bot_data.get("shopee")
        shopee.generate_short_link = AsyncMock(return_value="https://shope.ee/converted")

        next_state = await convert_link_message(mock_telegram_update, mock_telegram_context)

        assert next_state == ConversationHandler.END

    @pytest.mark.telegram
    @pytest.mark.asyncio
    async def test_convert_link_invalid(self, mock_telegram_update, mock_telegram_context):
        """Rejeita link inválido."""
        mock_telegram_update.callback_query = None
        mock_telegram_update.message = MagicMock()
        mock_telegram_update.message.text = "https://google.com"
        mock_telegram_update.message.reply_text = AsyncMock()
        mock_telegram_update.effective_user.id = 123456789

        next_state = await convert_link_message(mock_telegram_update, mock_telegram_context)

        assert next_state == AWAITING_LINK
        # Deve pedir novamente
        mock_telegram_update.message.reply_text.assert_called()

    @pytest.mark.telegram
    @pytest.mark.asyncio
    async def test_convert_link_timeout(self, mock_telegram_update, mock_telegram_context):
        """Lida com timeout da conversação."""
        mock_telegram_update.message = MagicMock()
        mock_telegram_update.message.reply_text = AsyncMock()

        next_state = await convert_link_timeout(mock_telegram_update, mock_telegram_context)

        assert next_state == ConversationHandler.END


class TestReportHandlers:
    """Testes para handlers de relatório."""

    @pytest.mark.telegram
    @pytest.mark.asyncio
    async def test_report_callback_success(self, mock_telegram_update, mock_telegram_context):
        """Relatório gera dados corretamente."""
        from src.bot.handlers import report_callback

        # Mock Shopee response
        shopee = mock_telegram_context.bot_data.get("shopee")
        shopee.get_conversion_report = AsyncMock(
            return_value={
                "data": {
                    "conversionReport": {
                        "nodes": [
                            {"commissionAmount": "10.50", "orderStatus": "PAID"},
                            {"commissionAmount": "5.00", "orderStatus": "CANCELLED"},
                        ]
                    }
                }
            }
        )

        # Mock edit_text on message (used in _generate_report)
        mock_telegram_update.callback_query.message = MagicMock()
        mock_telegram_update.callback_query.message.edit_text = AsyncMock()

        await report_callback(mock_telegram_update, mock_telegram_context)

        # Verifica chamada inicial (loading)
        mock_telegram_update.callback_query.edit_message_text.assert_called()

        # Verifica chamada final (relatório) no message object
        mock_telegram_update.callback_query.message.edit_text.assert_called()

        calls = mock_telegram_update.callback_query.message.edit_text.call_args_list
        last_call_args = calls[-1][0]
        text_sent = last_call_args[0]

        # Permite tanto '.' quanto ',' como separador decimal
        assert "Relatório de Comissões" in text_sent
        assert "15.50" in text_sent or "15,50" in text_sent

    @pytest.mark.telegram
    @pytest.mark.asyncio
    async def test_report_command_success(self, mock_telegram_update, mock_telegram_context):
        """Comando /relatorio funciona."""
        from src.bot.handlers import report_command

        # Configura message
        mock_telegram_update.callback_query = None
        mock_telegram_update.message = MagicMock()
        mock_telegram_update.message.reply_text = AsyncMock(return_value=MagicMock())
        # O retorno de reply_text é `msg`, que usa edit_text
        mock_telegram_update.message.reply_text.return_value.edit_text = AsyncMock()
        mock_telegram_update.effective_user.id = 123456789

        # Mock Shopee
        shopee = mock_telegram_context.bot_data.get("shopee")
        shopee.get_conversion_report = AsyncMock(
            return_value={"data": {"conversionReport": {"nodes": []}}}
        )

        await report_command(mock_telegram_update, mock_telegram_context)

        mock_telegram_update.message.reply_text.assert_called()
