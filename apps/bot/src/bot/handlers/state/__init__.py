from aiogram import Router
from .upload_cv import router as upload_cv_router
from .setup_search import router as setup_search_router

def get_state_router() -> Router:
    router = Router()
    router.include_routers(
        upload_cv_router,
        setup_search_router,
    )
    return router