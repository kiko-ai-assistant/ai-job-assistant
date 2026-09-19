from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from src.bot.handlers.commands.language import language
from src.bot.keyboard.inline_buttons.buttons import (
    create_vacancies_markup,
    create_vacancies_details_markup,
    create_vacancies_cv_markup,
    create_search_markup
)
from src.bot.utils.state_utils import collect_messages_to_delete

from src.locales.messages import MESSAGES

from src.services.database.main import Database
from src.services.database.models import User
from src.services.logs.logger import bot_logger

router = Router()


@router.callback_query(F.data == "refuse")
async def refuse_vacancy(call: types.CallbackQuery, state: FSMContext, user: User):
    msg_ids = [call.message.message_id]

    try:
        msg = await call.message.answer(
            text=MESSAGES[user.language]["vacancies_info"].format(
                title="Backend Developer", company="Startup Inc",
                salary="$110k", location="New York",
                match_score="88%", summary="Good match."
            ),
            reply_markup=create_vacancies_markup(current_language=user.language, url="https://hh.ru")
        )
        msg_ids.append(msg.message_id)
    except Exception as e:
        bot_logger.log_handler_error("refuse", e)
        msg = await call.message.answer(text=MESSAGES[user.language]["unknown_error"])
        msg_ids.append(msg.message_id)
    finally:
        await collect_messages_to_delete(state=state, data=msg_ids)


@router.callback_query(F.data == "details")
async def vacancy_details(call: types.CallbackQuery, state: FSMContext, user: User):
    msg = None
    
    try:
        msg = await call.message.answer(
            text=MESSAGES[user.language]["search_details"].format(
                description="Описание описание описание"
            ),
            reply_markup=create_vacancies_details_markup(current_language=user.language, url="https://hh.ru")
        )
    except Exception as e:
        bot_logger.log_handler_error("details", e)
        msg = await call.message.answer(text=MESSAGES[user.language]["unknown_error"])
    finally:
        if msg:
            await collect_messages_to_delete(state=state, data=msg.message_id)


@router.callback_query(F.data == "create_cv")
async def vacancy_create_cv(call: types.CallbackQuery, state: FSMContext, user: User):
    msg = None

    try:
        msg = await call.message.answer(
            text=MESSAGES[user.language]["search_cv"].format(
                description="Сгенеренное CV Сгенеренное CV Сгенеренное CV"
            ),
            reply_markup=create_vacancies_cv_markup(current_language=user.language, url="https://hh.ru")
        )
    except Exception as e:
        bot_logger.log_handler_error("create_cv", e)
        msg = await call.message.answer(text=MESSAGES[user.language]["unknown_error"])
    finally:
        if msg:
            await collect_messages_to_delete(state=state, data=msg.message_id)


@router.callback_query(F.data == "return")
async def vacancy_return(call: types.CallbackQuery, db: Database, state: FSMContext, user: User):
    msg = None

    try:
        settings = await db.user_settings.get_user_settings(user.id)
        skills_str = ", ".join(s.name for s in settings.skills) if settings and settings.skills else "Not specified"
        msg = await call.message.answer(
            text=MESSAGES[user.language]["vacancies_info"].format(
                title="Backend Developer", company="Startup Inc",
                salary="$110k", location="New York",
                match_score="88%", summary="Good match."
            ),
            reply_markup=create_vacancies_markup(current_language=user.language, url="https://hh.ru")
        )
    except Exception as e:
        bot_logger.log_handler_error("return", e)
        msg = await call.message.answer(text=MESSAGES[user.language]["unknown_error"])
    finally:
        if msg:
            await collect_messages_to_delete(state=state, data=msg.message_id)
