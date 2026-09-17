from pathlib import Path

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from src.bot.handlers.inline_buttons.main_menu import account
from src.bot.handlers.inline_buttons.account_menu import edit_cv
from src.bot.keyboard.reply_buttons.buttons import create_back_markup
from src.bot.keyboard.inline_buttons.buttons import create_delete_cv_markup
from src.bot.state.state_init import UploadCV
from src.bot.utils.state_utils import collect_messages_to_delete

from src.locales.messages import MESSAGES

from src.services.database.main import Database
from src.services.database.models import User
from src.services.logs.logger import bot_logger

from src.bot.utils.cv_utils import delete_cv as delete_cv_util

router = Router()


@router.callback_query(F.data == "upload_cv")
async def upload_cv(call: types.CallbackQuery, state: FSMContext, user: User):
    msg = None

    try:
        msg = await call.message.answer(
            text=MESSAGES[user.language]["upload_cv"],
            reply_markup=create_back_markup(current_language=user.language)
        )
        await state.set_state(UploadCV.get_cv)
    except Exception as e:
        bot_logger.log_handler_error("upload_cv", e)
        msg = await call.message.answer(
            text=MESSAGES[user.language]["unknown_error"]
        )
    finally:
        if msg:
            await collect_messages_to_delete(state=state, data=msg.message_id)


@router.callback_query(F.data == "delete_cv")
async def delete_cv(call: types.CallbackQuery, state: FSMContext, user: User):
    msg = None

    try:
        msg = await call.message.answer(
            text=MESSAGES[user.language]["delete_cv"],
            reply_markup=create_delete_cv_markup(current_language=user.language)
        )
    except Exception as e:
        bot_logger.log_handler_error("delete_cv", e)
        msg = await call.message.answer(
            text=MESSAGES[user.language]["unknown_error"]
        )
    finally:
        if msg:
            await collect_messages_to_delete(state=state, data=msg.message_id)


@router.callback_query(F.data == "delete_confirm")
async def delete_confirm(call: types.CallbackQuery, state: FSMContext, db: Database, user: User):
    msg = None

    try:
        await db.users.update_user_cv(
            user_id=user.id, cv_file_id=None, cv_path=None
        )

        delete_cv_util(cv_path=Path(user.cv_path))

        msg = await call.message.answer(
            text=MESSAGES[user.language]["cv_deleted"]
        )
    except Exception as e:
        bot_logger.log_handler_error("delete_confirm", e)
        msg = await call.message.answer(
            text=MESSAGES[user.language]["unknown_error"]
        )
    finally:
        await account(call=call, state=state, user=user)
        if msg:
            await collect_messages_to_delete(state=state, data=msg.message_id)


@router.callback_query(F.data == "delete_back")
async def delete_back(call: types.CallbackQuery, state: FSMContext, user: User):
    msg = None

    try:
        await edit_cv(call=call, state=state, user=user)
    except Exception as e:
        bot_logger.log_handler_error("delete_back", e)
        msg = await call.message.answer(
            text=MESSAGES[user.language]["unknown_error"]
        )
    finally:
        if msg:
            await collect_messages_to_delete(state=state, data=msg.message_id)


@router.callback_query(F.data == "edit_cv_back")
async def edit_cv_back(call: types.CallbackQuery, state: FSMContext, user: User):
    try:
        await account(call=call, state=state, user=user)
    except Exception as e:
        bot_logger.log_handler_error("account_back", e)
