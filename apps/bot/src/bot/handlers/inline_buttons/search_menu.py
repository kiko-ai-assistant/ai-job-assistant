from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from src.bot.handlers.inline_buttons.main_menu import search
from src.bot.handlers.state.setup_search import start_setup_search
from src.bot.keyboard.inline_buttons.buttons import (
    create_vacancies_markup,
    create_vacancies_details_markup,
)
from src.bot.utils.state_utils import collect_messages_to_delete

from src.locales.messages import MESSAGES

from src.services.database.main import Database
from src.services.database.models import User
from src.services.logs.logger import bot_logger

router = Router()


@router.callback_query(F.data == "vacancies")
async def refuse_vacancy(call: types.CallbackQuery, state: FSMContext, user: User):
    msg_ids = [call.message.message_id]

    try:

        # TODO: Add vacancy parsing
        # db.vacancies.get_vacancies(user_id=user.id)
        msg = await call.message.answer(
            text=MESSAGES[user.language]["vacancies_info"].format(
                title="Frontend Developer", company="Tech Corp",
                salary="$100k", location="Remote",
                match_score="95%", summary="Great match for your skills."
            ),
            reply_markup=create_vacancies_markup(current_language=user.language)
        )
        msg_ids.append(msg.message_id)
    except Exception as e:
        bot_logger.log_handler_error("vacancies", e)
        msg = await call.message.answer(text=MESSAGES[user.language]["unknown_error"])
        msg_ids.append(msg.message_id)
    finally:
        await collect_messages_to_delete(state=state, data=msg_ids)


@router.callback_query(F.data == "change_settings")
async def change_settings(call: types.CallbackQuery, state: FSMContext, user: User):
    msg_ids = [call.message.message_id]

    try:
        await start_setup_search(call.message, state, user)
    except Exception as e:
        bot_logger.log_handler_error("change_settings", e)
        msg = await call.message.answer(text=MESSAGES[user.language]["unknown_error"])
        msg_ids.append(msg.message_id)
    finally:
        await collect_messages_to_delete(state=state, data=msg_ids)


@router.callback_query(F.data == "search_menu")
async def search_menu(call: types.CallbackQuery, state: FSMContext, db: Database, user: User):
    try:
        await search(call=call, state=state, db=db, user=user)
    except Exception as e:
        bot_logger.log_handler_error("search_menu", e)
