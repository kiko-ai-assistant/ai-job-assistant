from aiogram import Router
from .unknown import router as unknown_router

def get_messages_router() -> Router:
    router = Router()
    router.include_routers(unknown_router)
    return router