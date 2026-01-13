"""Keyboards (InlineKeyboardMarkup) para o bot."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# Constantes para callback_data (evita strings mágicas)
class CallbackData:
    """Constantes para callback_data dos botões."""

    MENU = "menu"
    CURATE_NOW = "curate_now"
    CONVERT_LINK = "convert_link"
    STATUS = "status"
    HELP = "help"


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Retorna o teclado do menu principal."""
    keyboard = [
        [
            InlineKeyboardButton("🤖 Curadoria Agora", callback_data=CallbackData.CURATE_NOW),
            InlineKeyboardButton("🔗 Converter Link", callback_data=CallbackData.CONVERT_LINK),
        ],
        [
            InlineKeyboardButton("📊 Status", callback_data=CallbackData.STATUS),
            InlineKeyboardButton("⚙️ Ajuda", callback_data=CallbackData.HELP),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Retorna teclado com botão voltar ao menu."""
    keyboard = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data=CallbackData.MENU)]]
    return InlineKeyboardMarkup(keyboard)


def status_keyboard() -> InlineKeyboardMarkup:
    """Retorna teclado da tela de status."""
    keyboard = [
        [
            InlineKeyboardButton("🔄 Atualizar", callback_data=CallbackData.STATUS),
            InlineKeyboardButton("🔙 Menu", callback_data=CallbackData.MENU),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
