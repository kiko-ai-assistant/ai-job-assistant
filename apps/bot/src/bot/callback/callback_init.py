from aiogram.filters.callback_data import CallbackData


class SkillAction(CallbackData, prefix="sk", sep="_"):
    action: str  # Current action with the button, such as "select" or "page" or "back"
    name: str  # Name of the selected skill, for example, "Go", "Docker"
    category: str  # Current category of selected skill. May be "main" for common skills and special one for relative skills, e.g. "Python"
    page: int  # For pagination
    has_sub: bool  # Does it turn into submenu
