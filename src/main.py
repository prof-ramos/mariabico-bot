"""Entry point do MariaBicoBot."""

import asyncio
import signal
import sys
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from src.bot.formatters import format_consolidated_message
from src.bot.handlers import (
    AWAITING_LINK,
    convert_link_message,
    convert_link_start,
    curate_now_callback,
    help_callback,
    help_command,
    menu_callback,
    menu_command,
    report_callback,
    report_command,
    status_callback,
)
from src.bot.keyboards import CallbackData
from src.config import get_settings
from src.core import Curator, ScoreWeights
from src.database import Database, init_db
from src.shopee import ShopeeClient
from src.utils.logger import get_logger, setup_logger

logger = get_logger("mariabicobot", "main")


async def scheduled_curation(context):
    """Job de curadoria agendada.

    Args:
        context: Contexto do bot
    """
    logger.info("Iniciando curadoria agendada")

    settings = get_settings()
    db: Database = context.bot_data.get("db")
    shopee: ShopeeClient = context.bot_data.get("shopee")
    curator: Curator = context.bot_data.get("curator")

    if not all([db, shopee, curator]):
        logger.error("Sistema não disponível para curadoria agendada")
        return

    # Inicia run
    run_id = db.start_run("scheduled")

    try:
        # Configurações (TODO: carregar do banco)
        keywords = ["fone bluetooth", "smartwatch", "carregador rápido", "cabo usb", "fone ouvido"]
        categories = None

        # Executa curadoria
        result = await curator.curate(keywords, categories)

        # Envia no grupo
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
            batch_id = datetime.now().strftime("%Y%m%d_%H%M_scheduled")
            for product in result["products"]:
                item_id = product.get("itemId")
                short_link = product.get("shortLink", "")
                if item_id and short_link:
                    curator.deduplicator.mark_sent(
                        item_id, settings.target_group_id, short_link, batch_id
                    )

        # Finaliza run
        db.end_run(
            run_id,
            items_fetched=result["fetched"],
            items_approved=result["approved"],
            items_sent=result["final"],
            success=True,
        )

        logger.info(
            f"Curadoria agendada concluída: {result['fetched']} buscados, "
            f"{result['approved']} aprovados, {result['final']} enviados"
        )

    except Exception as e:
        logger.error(f"Erro na curadoria agendada: {e}")
        db.end_run(
            run_id,
            items_fetched=0,
            items_approved=0,
            items_sent=0,
            error_summary=str(e),
            success=False,
        )


def setup_scheduler(application: Application) -> AsyncIOScheduler:
    """Configura o scheduler para curadoria automática.

    Args:
        application: Aplicação do bot

    Returns:
        Scheduler configurado
    """
    settings = get_settings()
    scheduler = AsyncIOScheduler(timezone=settings.tz)

    # Usa CronTrigger para fazer parse robusto do cron
    trigger = CronTrigger.from_crontab(settings.schedule_cron, timezone=settings.tz)

    # Adiciona job de curadoria
    scheduler.add_job(
        scheduled_curation,
        trigger=trigger,
        id="curation_job",
        name="Curadoria Automática",
        args=(application,),
    )

    return scheduler


async def init_application() -> Application:
    """Inicializa a aplicação do bot.

    Returns:
        Application configurada
    """
    logger.info("Inicializando MariaBicoBot")

    # Carrega configurações
    settings = get_settings()
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Database: {settings.db_path}")
    logger.info(f"Admin user ID: {settings.admin_telegram_user_id}")
    logger.info(f"Target group ID: {settings.target_group_id}")

    # Inicializa banco de dados
    logger.info("Inicializando banco de dados...")
    conn = init_db(settings.db_path)
    db = Database(settings.db_path)

    # Inicializa cliente Shopee
    logger.info("Inicializando cliente Shopee API...")
    shopee = ShopeeClient(settings.shopee_app_id, settings.shopee_secret)

    # Inicializa curador
    logger.info("Inicializando curador...")
    curator = Curator(
        shopee_client=shopee,
        db=db,
        group_id=str(settings.target_group_id),
        group_hash="g1",  # TODO: configurável
        top_n=10,
        max_pages=5,
        page_limit=50,
        dedup_days=7,
        weights=ScoreWeights(),  # TODO: configurável
    )

    # Cria aplicação Telegram
    logger.info("Inicializando bot Telegram...")
    application = Application.builder().token(settings.telegram_bot_token).build()

    # Armazena dependências no bot_data
    application.bot_data["db"] = db
    application.bot_data["shopee"] = shopee
    application.bot_data["curator"] = curator

    # Registra handlers
    application.add_handler(CommandHandler("start", menu_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("relatorio", report_command))

    # Callback handlers
    application.add_handler(CallbackQueryHandler(menu_callback, pattern=f"^{CallbackData.MENU}$"))
    application.add_handler(
        CallbackQueryHandler(status_callback, pattern=f"^{CallbackData.STATUS}$")
    )
    application.add_handler(
        CallbackQueryHandler(report_callback, pattern=f"^{CallbackData.REPORT}$")
    )
    application.add_handler(
        CallbackQueryHandler(curate_now_callback, pattern=f"^{CallbackData.CURATE_NOW}$")
    )
    application.add_handler(CallbackQueryHandler(help_callback, pattern=f"^{CallbackData.HELP}$"))

    # Conversação de conversão de link
    # Importante: deve ser registrado ANTES de outros MessageHandlers
    convert_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(convert_link_start, pattern=f"^{CallbackData.CONVERT_LINK}$"),
            CommandHandler("converter", convert_link_start),
        ],
        states={
            AWAITING_LINK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, convert_link_message),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(menu_callback, pattern=f"^{CallbackData.MENU}$"),
        ],
        conversation_timeout=60,
        map_to_parent={
            ConversationHandler.END: ConversationHandler.END,
        },
        allow_reentry=True,
    )

    # Registra o ConversationHandler (tem prioridade sobre outros handlers)
    application.add_handler(convert_conv)

    logger.info("Bot configurado com sucesso")

    return application


async def main():
    """Função principal."""
    # Carrega configurações primeiro para pegar o log level
    settings = get_settings()

    # Setup logger global com o nível configurado
    setup_logger("mariabicobot", level=settings.log_level)

    logger.info("=" * 50)
    logger.info("MariaBicoBot v1.0.0")
    logger.info("=" * 50)

    try:
        # Inicializa aplicação
        application = await init_application()

        # Configura scheduler
        scheduler = setup_scheduler(application)
        scheduler.start()
        logger.info("Scheduler iniciado")

        # Handlers de shutdown
        def signal_handler(sig, frame):
            logger.info(f"Recebido sinal {sig}, encerrando...")
            scheduler.shutdown()
            asyncio.create_task(shutdown(application))

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Inicia bot
        logger.info("Iniciando bot (polling)...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)

        logger.info("Bot rodando. Pressione Ctrl+C para encerrar.")

        # Mantém rodando
        await asyncio.Event().wait()

    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        sys.exit(1)


async def shutdown(application: Application):
    """Encerra a aplicação gracefulmente.

    Args:
        application: Aplicação do bot
    """
    logger.info("Encerrando bot...")

    # Para o updater
    if application.updater.running:
        await application.updater.stop()

    # Para a aplicação
    await application.stop()
    await application.shutdown()

    # Fecha cliente Shopee
    shopee: ShopeeClient = application.bot_data.get("shopee")
    if shopee:
        await shopee.close()

    # Fecha banco
    db: Database = application.bot_data.get("db")
    if db:
        db.close()

    logger.info("Bot encerrado")


if __name__ == "__main__":
    asyncio.run(main())
