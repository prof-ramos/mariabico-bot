"""Formatação de mensagens do bot."""

from datetime import datetime


def format_product_message(product: dict, short_link: str) -> str:
    """Formata mensagem de produto individual.

    Args:
        product: Dicionário com dados do produto
        short_link: Short link do produto

    Returns:
        Mensagem formatada em HTML
    """
    name = product.get("productName", "")[:80]
    price = product.get("priceMin", 0)
    discount = product.get("priceDiscountRate", 0)
    commission = product.get("commission", 0)
    commission_rate = product.get("commissionRate", 0) * 100
    keyword = product.get("keyword", "").replace(" ", "")

    return (
        f"🛒 <b>{name}</b>\n\n"
        f"💰 R$ {price:.2f} | 🔻 {discount}% OFF\n"
        f"💸 Comissão: R$ {commission:.2f} ({commission_rate:.1f}%)\n\n"
        f"🔗 {short_link}\n\n"
        f"#{keyword} #shopee #oferta"
    )


def format_consolidated_message(products: list, context: dict) -> str:
    """Formata mensagem consolidada com Top N produtos.

    Args:
        products: Lista de produtos formatados
        context: Dicionário com contexto (fetched, approved, etc)

    Returns:
        Mensagem formatada em HTML
    """
    now = datetime.now()
    header = (
        f"🤖 <b>Curadoria MariaBicoBot</b>\n"
        f"📅 {now.strftime('%d/%m/%Y')} às {now.strftime('%H:%M')}\n\n"
        f"🏆 Top {len(products)} Produtos Selecionados:\n"
    )

    items = []
    for i, product in enumerate(products, 1):
        name = product.get("productName", "")[:50]
        price = product.get("priceMin", 0)
        discount = product.get("priceDiscountRate", 0)
        commission = product.get("commission", 0)
        short_link = product.get("shortLink", "")

        item = (
            f"\n{'━' * 40}\n"
            f"{i}️⃣ <b>{name}</b>\n"
            f"💰 R$ {price:.2f} | 🔻 {discount}% | 💸 R$ {commission:.2f}\n"
            f"🔗 {short_link}"
        )
        items.append(item)

    footer = (
        f"\n\n📊 Avaliados: {context.get('fetched', 0)} | Aprovados: {context.get('approved', 0)}"
    )

    return header + "".join(items) + footer


def format_status_message(stats: dict) -> str:
    """Formata mensagem de status do sistema.

    Args:
        stats: Dicionário com estatísticas

    Returns:
        Mensagem formatada em HTML
    """
    is_healthy = stats.get("is_healthy", True)
    status_emoji = "✅" if is_healthy else "⚠️"
    status_text = "operacional" if is_healthy else "com problemas"

    last_run = stats.get("last_run", {})
    last_run_text = "Nenhuma execução ainda"
    if last_run:
        last_run_text = f"{last_run.get('started_at', 'N/A')}"
        last_run_text += f"\n• Avaliados: {last_run.get('items_fetched', 0)} produtos"
        last_run_text += f"\n• Aprovados: {last_run.get('items_approved', 0)} produtos"
        last_run_text += f"\n• Enviados: {last_run.get('items_sent', 0)} produtos"
        success_rate = last_run.get("success_rate", 100)
        last_run_text += f"\n• Taxa sucesso: {success_rate}%"

    next_run = stats.get("next_run", {})
    next_run_text = "Agendamento configurado"
    if next_run:
        next_run_text = f"{next_run.get('scheduled_at', 'N/A')}"

    db_stats = stats.get("db_stats", {})
    db_text = "0 produtos, 0 links, 0 envios"
    if db_stats:
        db_text = (
            f"• Produtos únicos: {db_stats.get('unique_products', 0):,}\n"
            f"• Links gerados: {db_stats.get('total_links', 0):,}\n"
            f"• Envios realizados: {db_stats.get('total_sent_messages', 0):,}"
        )

    return (
        f"📊 <b>Status do MariaBicoBot</b>\n\n"
        f"{status_emoji} Sistema {status_text}\n"
        f"🕐 Uptime: {stats.get('uptime', 'N/A')}\n\n"
        f"📦 <b>Última Curadoria</b>\n"
        f"{last_run_text}\n\n"
        f"⏭️ <b>Próxima Execução</b>\n"
        f"• Agendada para: {next_run_text}\n"
        f"• Tipo: Curadoria automática\n\n"
        f"⚡ <b>Rate Limit API Shopee</b>\n"
        f"• Usado: {stats.get('rate_limit_used', 0)} / 2000 req/h\n"
        f"• Disponível: {2000 - stats.get('rate_limit_used', 0)} req/h\n\n"
        f"💾 <b>Banco de Dados</b>\n"
        f"{db_text}\n\n"
        f"⚠️ Erros (últimas 24h): {stats.get('errors_24h', 0)}"
    )


def format_help_message() -> str:
    """Retorna mensagem de ajuda.

    Returns:
        Mensagem formatada em HTML
    """
    return (
        "⚙️ <b>Ajuda - MariaBicoBot</b>\n\n"
        "<b>Comandos disponíveis:</b>\n"
        "/start ou /menu - Abre o menu principal\n"
        "/status - Mostra status do sistema\n"
        "/converter - Converte link Shopee manualmente\n\n"
        "<b>Menu:</b>\n"
        "🤖 <b>Curadoria Agora</b> - Executa curadoria imediata\n"
        "🔗 <b>Converter Link</b> - Gera link rastreável\n"
        "📊 <b>Status</b> - Mostra estatísticas\n"
        "⚙️ <b>Ajuda</b> - Esta mensagem\n\n"
        "<b>Funcionalidades:</b>\n"
        "• Curadoria automática a cada 12h\n"
        "• Links rastreáveis com subIds\n"
        "• Deduplicação de produtos\n"
        "• Rankeamento por score"
    )


def format_report_message(report_data: dict, period_days: int) -> str:
    """Formata mensagem de relatório de comissões.

    Args:
        report_data: Dados agregados do relatório
        period_days: Período em dias

    Returns:
        Mensagem formatada em HTML
    """
    # Coerção defensiva para valores None/falsy
    total_orders = report_data.get("total_orders") or 0
    total_commission = report_data.get("total_commission") or 0.0
    paid_orders = report_data.get("paid_orders") or 0

    # Conversões e taxas (evita divisão por zero)
    conversion_rate = 0.0
    if total_orders > 0:
        conversion_rate = (paid_orders / total_orders) * 100

    return (
        f"💸 <b>Relatório de Comissões</b>\n"
        f"📅 Últimos {period_days} dias\n\n"
        f"💰 <b>Estimativa:</b> R$ {total_commission:.2f}\n"
        f"📦 <b>Pedidos Totais:</b> {total_orders}\n"
        f"✅ <b>Pedidos Pagos:</b> {paid_orders}\n"
        f"📈 <b>Taxa Conversão:</b> {conversion_rate:.1f}%\n\n"
        f"<i>* Valores estimados baseados na API de conversão.</i>"
    )
