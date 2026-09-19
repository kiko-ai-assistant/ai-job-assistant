from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from src.bot.handlers.commands.menu import menu
from src.bot.handlers.state.setup_search import start_setup_search

from src.bot.keyboard.inline_buttons.buttons import create_account_menu_markup
from src.bot.keyboard.inline_buttons.buttons import create_search_markup
from src.bot.utils.state_utils import collect_messages_to_delete

from src.locales.messages import MESSAGES

from src.services.database.models import User
from src.services.database.main import Database
from src.services.logs.logger import bot_logger

router = Router()


@router.callback_query(F.data == "main_menu")
async def main_menu(call: types.CallbackQuery, state: FSMContext, user: User):
    try:
        await menu(message=call.message, state=state, user=user)
    except Exception as e:
        bot_logger.log_handler_error("main_menu", e)


@router.callback_query(F.data == "search")
async def search(call: types.CallbackQuery, state: FSMContext, db: Database, user: User):
    msg = None

    try:
        if not user.cv_file_id:
            await call.answer(text=MESSAGES[user.language]["search_not_available"])
            return

        settings = await db.user_settings.get_user_settings(user.id)
        if not settings:
            await start_setup_search(call.message, state, user)
            return

        skills_str = ", ".join(s.name for s in settings.skills) if settings.skills else "Not specified"

        msg = await call.message.answer(
            text=MESSAGES[user.language]["search_info"].format(
                skills=skills_str, grade=settings.grade,
                job_type=settings.job_type, location=settings.location
            ),
            reply_markup=create_search_markup(current_language=user.language)
        )

    except Exception as e:
        bot_logger.log_handler_error("search", e)
        msg = await call.message.answer(text=MESSAGES[user.language]["unknown_error"])
    finally:
        if msg:
            await collect_messages_to_delete(state=state, data=msg.message_id)


@router.callback_query(F.data == "account")
async def account(call: types.CallbackQuery, state: FSMContext, user: User):
    msg = None

    try:
        msg = await call.message.answer(
            text=MESSAGES[user.language]["account_info"].format(
                id=user.id, name=user.first_name, lang=user.language,
                cv_set=('✅' if user.cv_file_id is not None else '❌'),
                created_at=user.created_at.strftime("%Y-%m-%d")
            ),
            reply_markup=create_account_menu_markup(current_language=user.language)
        )
    except Exception as e:
        bot_logger.log_handler_error("account", e)
        msg = await call.message.answer(text=MESSAGES[user.language]["unknown_error"])
    finally:
        if msg:
            await collect_messages_to_delete(state=state, data=msg.message_id)
