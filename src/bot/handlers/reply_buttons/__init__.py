from aiogram import Router

def get_reply_buttons_router() -> Router:
    router = Router()
    router.include_routers()
    return router