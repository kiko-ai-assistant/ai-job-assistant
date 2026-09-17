from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from src.locales.reply_buttons import REPLY_BUTTONS
from src.config import DEFAULT_LANGUAGE


def create_back_markup(current_language: str = DEFAULT_LANGUAGE) -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(keyboard=[
        [
            KeyboardButton(text=REPLY_BUTTONS[current_language]["back_button"])
        ]
    ], resize_keyboard=True)
    return markup
