from aiogram import Router
from src.bot.handlers.commands import get_commands_router
# from src.bot.handlers.reply_buttons import get_reply_buttons_router
from src.bot.handlers.messages import get_messages_router
from src.bot.handlers.inline_buttons import get_inline_buttons_router
from src.bot.handlers.state import get_state_router

def get_main_router() -> Router:
    router = Router()
    router.include_routers(
        get_commands_router(),
        # get_reply_buttons_router(),
        get_inline_buttons_router(),
        get_state_router(),
        get_messages_router(),
    )
    return router