"""Handlers para comandos e callbacks do bot."""

from datetime import datetime
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.bot.formatters import (
    format_consolidated_message,
    format_help_message,
    format_product_message,
    format_status_message,
)
from src.bot.keyboards import (
    back_to_menu_keyboard,
    CallbackData,
    main_menu_keyboard,
    status_keyboard,
)
from src.bot.validators import escape_html, is_valid_shopee_url, normalize_shopee_url
from src.config import get_settings
from src.core import Curator
from src.database import Database
from src.shopee import ShopeeClient
from src.utils.logger import get_logger

logger = get_logger("mariabicobot", "bot")

# Estados da conversação de conversão de link
AWAITING_LINK = 1


async def is_authorized(user_id: int) -> bool:
    """Verifica se usuário está autorizado.

    Args:
        user_id: ID do usuário Telegram

    Returns:
        True se autorizado
    """
    settings = get_settings()
    is_auth = user_id == settings.admin_telegram_user_id
    if not is_auth:
        logger.warning(
            f"Unauthorized access attempt: {user_id} (Admin is {settings.admin_telegram_user_id})"
        )
    return is_auth


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para comando /start e /menu.

    Args:
        update: Update do Telegram
        context: Contexto do bot
    """
    if not update.message:
        return

    logger.info(
        f"Recebido {update.message.text} de {update.effective_user.id} no chat {update.effective_chat.id}"
    )

    if not await is_authorized(update.effective_user.id):
        return

    text = (
        "🤖 <b>MariaBicoBot</b>\n"
        "Bot de Curadoria Shopee Afiliados\n\n"
        "Escolha uma opção:"
    )

    await update.message.reply_text(
        text,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )

    logger.info(f"Usuário {update.effective_user.id} abriu o menu")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para comando /help.

    Args:
        update: Update do Telegram
        context: Contexto do bot
    """
    if not update.message or not await is_authorized(update.effective_user.id):
        return

    await update.message.reply_text(
        format_help_message(),
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback para botão do menu.

    Args:
        update: Update do Telegram
        context: Contexto do bot
    """
    query = update.callback_query
    if not query or not await is_authorized(query.from_user.id):
        return

    await query.answer()

    text = (
        "🤖 <b>MariaBicoBot</b>\n"
        "Bot de Curadoria Shopee Afiliados\n\n"
        "Escolha uma opção:"
    )

    await query.edit_message_text(
        text,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )


async def status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback para botão de status.

    Args:
        update: Update do Telegram
        context: Contexto do bot
    """
    query = update.callback_query
    if not query or not await is_authorized(query.from_user.id):
        return

    await query.answer()

    # Busca estatísticas
    settings = get_settings()
    db: Database = context.bot_data.get("db")
    shopee: ShopeeClient = context.bot_data.get("shopee")

    if not db:
        await query.edit_message_text("⚠️ Banco de dados não disponível")
        return

    # Busca última execução
    last_run = db.get_last_run()
    last_run_data = {}
    if last_run:
        last_run_data = {
            "started_at": last_run.started_at,
            "items_fetched": last_run.items_fetched,
            "items_approved": last_run.items_approved,
            "items_sent": last_run.items_sent,
            "success_rate": 100 if last_run.success else 0,
        }

    # Estatísticas do banco
    db_stats = db.get_stats()

    stats = {
        "is_healthy": True,
        "uptime": "Calculando...",  # TODO: implementar uptime real
        "last_run": last_run_data,
        "next_run": {"scheduled_at": "Configurado no cron"},
        "rate_limit_used": 0,  # TODO: implementar rate limit tracking
        "db_stats": db_stats,
        "errors_24h": 0,  # TODO: implementar error tracking
    }

    text = format_status_message(stats)

    await query.edit_message_text(
        text,
        reply_markup=status_keyboard(),
        parse_mode="HTML",
    )


async def curate_now_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Callback para botão de curadoria imediata.

    Args:
        update: Update do Telegram
        context: Contexto do bot
    """
    query = update.callback_query
    if not query or not await is_authorized(query.from_user.id):
        return

    await query.answer()

    # Envia mensagem de processamento
    await query.edit_message_text("⚙️ Executando curadoria...")

    # Executa curadoria
    try:
        settings = get_settings()
        db: Database = context.bot_data.get("db")
        shopee: ShopeeClient = context.bot_data.get("shopee")
        curator: Curator = context.bot_data.get("curator")

        if not all([db, shopee, curator]):
            await query.edit_message_text("⚠️ Sistema não disponível")
            return

        # Configurações padrão (TODO: carregar do banco)
        keywords = ["fone bluetooth", "smartwatch", "carregador rápido"]
        categories = None

        # Executa curadoria
        result = await curator.curate(keywords, categories)

        # Envia resultado no grupo
        if result["products"]:
            message = format_consolidated_message(
                result["products"],
                {
                    "fetched": result["fetched"],
                    "approved": result["approved"],
                },
            )

            await context.bot.send_message(
                chat_id=settings.target_group_id,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )

            # Marca produtos como enviados
            batch_id = datetime.now().strftime("%Y%m%d_%H%M_manual")
            for product in result["products"]:
                item_id = product.get("itemId")
                short_link = product.get("shortLink", "")
                if item_id and short_link:
                    curator.deduplicator.mark_sent(
                        item_id, settings.target_group_id, short_link, batch_id
                    )

            await query.edit_message_text(
                f"✅ Curadoria concluída!\n\n"
                f"📦 Avaliados: {result['fetched']}\n"
                f"✅ Aprovados: {result['approved']}\n"
                f"📤 Enviados: {result['final']}\n\n"
                f"Verifique o grupo!",
                reply_markup=back_to_menu_keyboard(),
            )
        else:
            await query.edit_message_text(
                f"⚠️ Nenhum produto aprovado.\n\n"
                f"Avaliados: {result['fetched']}\n"
                f"Aprovados: {result['approved']}",
                reply_markup=back_to_menu_keyboard(),
            )

    except Exception as e:
        logger.error(f"Erro na curadoria: {e}")
        await query.edit_message_text(
            f"❌ Erro na curadoria: {escape_html(str(e))}",
            reply_markup=back_to_menu_keyboard(),
        )


async def convert_link_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia conversação de conversão de link.

    Args:
        update: Update do Telegram
        context: Contexto do bot

    Returns:
        Próximo estado da conversação
    """
    query = update.callback_query
    if not query or not await is_authorized(query.from_user.id):
        return ConversationHandler.END

    await query.answer()

    await query.edit_message_text(
        "📎 <b>Converter Link</b>\n\n"
        "Envie o link do produto Shopee que deseja converter.\n\n"
        "⏱️ Aguardando link... (60s)",
        parse_mode="HTML",
    )

    return AWAITING_LINK


async def convert_link_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Processa link enviado pelo usuário.

    Args:
        update: Update do Telegram
        context: Contexto do bot

    Returns:
        Fim da conversação
    """
    if not update.message or not await is_authorized(update.effective_user.id):
        return ConversationHandler.END

    url = update.message.text.strip()

    # Validação
    if not is_valid_shopee_url(url):
        await update.message.reply_text(
            "❌ Link inválido. Envie um link Shopee válido.\n\n"
            "Exemplo: https://shopee.com.br/product/..."
        )
        return AWAITING_LINK

    # Indicador de processamento
    msg = await update.message.reply_text("⚙️ Gerando link rastreável...")

    try:
        # Normaliza URL
        normalized_url = normalize_shopee_url(url)

        # Gera short link
        shopee: ShopeeClient = context.bot_data.get("shopee")
        db: Database = context.bot_data.get("db")

        if not shopee or not db:
            await msg.edit_text("⚠️ Sistema não disponível")
            return ConversationHandler.END

        # Verifica cache
        cached = db.get_cached_link(normalized_url)
        if cached:
            short_link = cached.short_link
        else:
            # Gera novo link
            from src.core import build_sub_ids

            settings = get_settings()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            sub_ids = build_sub_ids("manual", "default", timestamp, "")

            short_link = await shopee.generate_short_link(normalized_url, sub_ids)
            db.get_or_create_link(normalized_url, short_link, sub_ids)

        # Resposta
        keyboard = back_to_menu_keyboard()

        await msg.edit_text(
            f"✅ <b>Link convertido com sucesso!</b>\n\n"
            f"🔗 {short_link}\n\n"
            f"📋 Copie e compartilhe!",
            parse_mode="HTML",
            reply_markup=keyboard,
        )

        logger.info(
            f"Link convertido para usuário {update.effective_user.id}: {normalized_url[:50]}"
        )

    except Exception as e:
        logger.error(f"Erro ao converter link: {e}")
        await msg.edit_text(
            f"⚠️ <b>Erro ao gerar link</b>\n\n"
            f"Detalhes: {escape_html(str(e))}\n\n"
            f"Tente novamente em instantes.",
            parse_mode="HTML",
        )

    return ConversationHandler.END


async def convert_link_timeout(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handler para timeout da conversação.

    Args:
        update: Update do Telegram
        context: Contexto do bot

    Returns:
        Fim da conversação
    """
    if update.message:
        await update.message.reply_text(
            "⏱️ Tempo expirado. Use /converter para tentar novamente.",
            reply_markup=main_menu_keyboard(),
        )
    return ConversationHandler.END


async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback para botão de ajuda.

    Args:
        update: Update do Telegram
        context: Contexto do bot
    """
    query = update.callback_query
    if not query or not await is_authorized(query.from_user.id):
        return

    await query.answer()

    await query.edit_message_text(
        format_help_message(),
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
