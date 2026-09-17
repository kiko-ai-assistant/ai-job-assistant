from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from src.services.logs.logger import AppLogger, bot_logger


class ChatCleanerMiddleware(BaseMiddleware):
    """This middleware cleans chat regularly - after each event caused by user"""
    def __init__(self, logger: AppLogger = bot_logger):
        self._logger = logger

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        state: FSMContext = data.get("state")
        if state:
            state_data = await state.get_data()
            msg_to_delete = state_data.get("messages_to_delete", set())

            if msg_to_delete:
                bot: Bot = data["bot"]

                if event.message:
                    chat_id = event.message.chat.id
                else:
                    chat_id = event.callback_query.message.chat.id

                try:
                    await bot.delete_messages(chat_id=chat_id, message_ids=list(msg_to_delete))
                except Exception as e:
                    self._logger.log_middleware_error(err=e)

            await state.update_data(messages_to_delete=set())
        return await handler(event, data)