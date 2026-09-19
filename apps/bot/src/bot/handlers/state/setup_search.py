from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from src.bot.state.state_init import SearchSettings
from src.bot.keyboard.inline_buttons.buttons import create_search_markup

from src.locales.messages import MESSAGES

from src.services.database.main import Database
from src.services.database.models import User
from src.services.logs.logger import bot_logger


router = Router()


async def start_setup_search(message: types.Message, state: FSMContext, user: User):
    await state.set_state(SearchSettings.get_skills)
    msg = await message.answer(text=MESSAGES[user.language]["get_skills"])
    await state.update_data(messages_to_delete={msg.message_id})


@router.message(SearchSettings.get_skills)
async def get_skills(message: types.Message, state: FSMContext, user: User):
    msg_ids = [message.message_id]

    try:
        skills_text = message.text
        skills_list = [{"name": s.strip(), "level": "Middle", "experience_years": 1.0} for s in skills_text.split(",") if s.strip()]

        await state.update_data(skills=skills_list)
        await state.set_state(SearchSettings.get_grade)

        msg = await message.answer(text=MESSAGES[user.language]["setup_grade"])

        data = await state.get_data()
        messages_to_delete = data.get("messages_to_delete", set())
        messages_to_delete.update({message.message_id, msg.message_id})
        await state.update_data(messages_to_delete=messages_to_delete)
    except Exception as e:
        bot_logger.log_handler_error("get_skills", e)
        msg = await message.answer(text=MESSAGES[user.language]["unknown_error"])
    finally:




@router.message(SearchSettings.get_grade)
async def setup_grade(message: types.Message, state: FSMContext, user: User):
    await state.update_data(grade=message.text)
    await state.set_state(SearchSettings.get_job_type)
    
    msg = await message.answer(text=MESSAGES[user.language]["setup_job_type"])
    
    data = await state.get_data()
    messages_to_delete = data.get("messages_to_delete", set())
    messages_to_delete.update({message.message_id, msg.message_id})
    await state.update_data(messages_to_delete=messages_to_delete)


@router.message(SearchSettings.get_job_type)
async def setup_job_type(message: types.Message, state: FSMContext, user: User):
    await state.update_data(job_type=message.text)
    await state.set_state(SearchSettings.get_location)
    
    msg = await message.answer(text=MESSAGES[user.language]["setup_location"])
    
    data = await state.get_data()
    messages_to_delete = data.get("messages_to_delete", set())
    messages_to_delete.update({message.message_id, msg.message_id})
    await state.update_data(messages_to_delete=messages_to_delete)


@router.message(SearchSettings.get_location)
async def setup_location(message: types.Message, db: Database, state: FSMContext, user: User):
    await state.update_data(location=message.text)
    data = await state.get_data()
    
    skills = data.get("skills", [])
    grade = data.get("grade", "")
    job_type = data.get("job_type", "")
    location = data.get("location", "")
    
    try:
        user_settings = await db.user_settings.get_user_settings(user.id)
        if user_settings:
            await db.user_settings.update_user_settings(user.id, skills=skills, grade=grade, job_type=job_type, location=location)
        else:
            await db.user_settings.create_user_settings(user.id, skills=skills, grade=grade, job_type=job_type, location=location)
            
        await message.answer(text=MESSAGES[user.language]["setup_complete"])
        
        skills_str = ", ".join(s["name"] for s in skills)
        msg = await message.answer(
            text=MESSAGES[user.language]["search_info"].format(
                skills=skills_str, grade=grade,
                job_type=job_type, location=location
            ),
            reply_markup=create_search_markup(current_language=user.language)
        )
        
    except Exception as e:
        bot_logger.log_handler_error("setup_location", e)
        msg = await message.answer(text=MESSAGES[user.language]["unknown_error"])
        
    finally:
        await state.clear()
        messages_to_delete = data.get("messages_to_delete", set())
        messages_to_delete.add(message.message_id)
        
        try:
            await message.bot.delete_messages(
                chat_id=message.chat.id,
                message_ids=list(messages_to_delete)
            )
        except Exception:
            pass
