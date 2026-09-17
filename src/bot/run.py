import asyncio

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.bot.middlewares.user_context import UserContextMiddleware
from src.bot.middlewares.chat_cleaner import ChatCleanerMiddleware
from src.bot.handlers import get_main_router

from src.config import BOT_TOKEN, load_db_config

from src.services.database.main import Database
from src.services.logs.logger import bot_logger


async def main():
    bot_logger.info("🧑‍💻 Developed by https://github.com/maket12")

    bot_logger.info("⚙️ Initialising bot and database...")
    # await asyncio.sleep(1)

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    db = Database(dsn=load_db_config())

    bot_logger.info("🛜 Connecting to Telegram...")
    # await asyncio.sleep(1)

    dp = Dispatcher()
    dp.update.outer_middleware(UserContextMiddleware(db))
    dp.update.outer_middleware(ChatCleanerMiddleware())
    dp.include_router(router=get_main_router())

    try:
        bot_logger.debug(f"🤖 Bot is starting...")
        await db.connect()
        await dp.start_polling(bot)
    except Exception as e:
        bot_logger.critical(f"💥 CRITICAL ERROR OCCURRED: {e}")
    finally:
        bot_logger.info("🔁 Closing database and telegram connections...")

        await db.disconnect()
        await bot.session.close()

        bot_logger.info("🎉 Bot stopped successfully")


if __name__ == "__main__":
    asyncio.run(main())
