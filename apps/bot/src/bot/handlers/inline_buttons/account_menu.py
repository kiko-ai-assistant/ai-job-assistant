from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from src.bot.handlers.commands.language import language
from src.bot.keyboard.inline_buttons.buttons import create_edit_cv_markup
from src.bot.utils.state_utils import collect_messages_to_delete

from src.locales.messages import MESSAGES

from src.services.database.models import User
from src.services.logs.logger import bot_logger

router = Router()


@router.callback_query(F.data == "change_language")
async def change_language(call: types.CallbackQuery, state: FSMContext, user: User):
    msg = None

    try:
        await language(message=call.message, state=state, user=user)
    except Exception as e:
        bot_logger.log_handler_error("change_language", e)
        msg = await call.message.answer(
            text=MESSAGES[user.language]["unknown_error"]
        )
    finally:
        if msg:
            await collect_messages_to_delete(state=state, data=msg.message_id)


@router.callback_query(F.data == "edit_cv")
async def edit_cv(call: types.CallbackQuery, state: FSMContext, user: User):
    msg_ids = []

    try:
        if user.cv_file_id:
            m1 = await call.message.answer_document(
                document=user.cv_file_id,
                caption=MESSAGES[user.language]["current_cv"]
            )
            msg_ids.append(m1.message_id)

        m2 = await call.message.answer(
            text=MESSAGES[user.language]["edit_cv"],
            reply_markup=create_edit_cv_markup(
                current_language=user.language,
                cv_set=bool(user.cv_file_id)
            )
        )
        msg_ids.append(m2.message_id)
    except Exception as e:
        bot_logger.log_handler_error("edit_cv", e)
        m1 = await call.message.answer(
            text=MESSAGES[user.language]["unknown_error"]
        )
        msg_ids.append(m1.message_id)
    finally:
        await collect_messages_to_delete(state=state, data=msg_ids)
