from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery, Message, User as TgUser

from src.services.database.main import Database
from src.services.logs.logger import AppLogger, bot_logger

from src.bot.handlers.commands.start import start

class UserContextMiddleware(BaseMiddleware):
    """This middleware stores objects such as Database and User into handler data"""
    def __init__(self, db: Database, logger: AppLogger = bot_logger):
        self._db = db
        self._logger = logger

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        data["db"] = self._db
        tg_user: Optional[TgUser] = data.get("event_from_user")

        real_event = event.message or event.callback_query

        if tg_user:
            user = None
            try:
                user = await self._db.users.get_user(tg_user.id)
            except Exception as e:
                self._logger.log_middleware_error(e)

            if isinstance(real_event, Message) and user is None and real_event.text != "/start":
                self._logger.warning(
                    f"⚠️ WARNING: User {real_event.from_user.id} is not in database "
                    f"but tried to call method")
                return await start(message=real_event, db=self._db, user=None)

            if isinstance(real_event, CallbackQuery) and user is None:
                self._logger.warning(
                    f"⚠️ WARNING: User {real_event.message.from_user.id} is not in database "
                    f"but tried to call method")
                await real_event.message.delete()
                return await start(message=real_event.message, db=self._db, user=None)

            data["user"] = user

        return await handler(event, data)
