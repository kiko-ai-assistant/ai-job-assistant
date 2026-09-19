from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.bot.keyboard.inline_buttons.buttons import create_change_language_markup
from src.bot.utils.state_utils import collect_messages_to_delete

from src.locales.messages import MESSAGES

from src.services.database.models import User
from src.services.logs.logger import bot_logger

router = Router()


@router.message(Command("language"))
async def language(message: types.Message, state: FSMContext, user: User):
    msgs_to_delete = [message.message_id]

    try:
        msg = await message.answer(
            text=MESSAGES[user.language]["language"],
            reply_markup=create_change_language_markup(current_language=user.language),
        )
        msgs_to_delete.append(msg.message_id)
    except Exception as e:
        bot_logger.log_handler_error("language", e)
        msg = await message.answer(text=MESSAGES[user.language]["unknown_error"])
        msgs_to_delete.append(msg.message_id)
    finally:
        await collect_messages_to_delete(state=state, data=msgs_to_delete)
