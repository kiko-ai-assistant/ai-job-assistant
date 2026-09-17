from typing import Optional

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from src.bot.handlers.commands.menu import menu
from src.bot.utils.state_utils import collect_messages_to_delete

from src.locales.messages import MESSAGES

from src.services.database.models import User
from src.services.logs.logger import bot_logger

router = Router()


@router.message()
async def unknown(message: types.Message, state: FSMContext, user: Optional[User]):
    msg_ids = [message.message_id]

    try:
        msg = await message.answer(text=MESSAGES[user.language]["unknown"])
        msg_ids.append(msg.message_id)
    except Exception as e:
        bot_logger.log_handler_error("unknown", e)
        msg = await message.answer(text=MESSAGES[user.language]["unknown_error"])
        msg_ids.append(msg.message_id)
    finally:
        await collect_messages_to_delete(state=state, data=msg_ids)
        await menu(message=message, state=state, user=user)
