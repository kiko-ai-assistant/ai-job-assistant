from aiogram.fsm.state import State, StatesGroup


class UploadCV(StatesGroup):
    get_cv = State()


class SearchSettings(StatesGroup):
    get_skills = State()
    get_grade = State()
    get_job_type = State()
    get_location = State()
