from aiogram import Router
from .start import router as start_router
from .language import router as language_router
from .menu import router as menu_router

def get_commands_router() -> Router:
    router = Router()
    router.include_routers(
        start_router, language_router,
        menu_router,
    )
    return router