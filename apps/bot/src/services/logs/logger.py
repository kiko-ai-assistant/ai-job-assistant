import logging
from datetime import datetime

import colorlog
from src.config import LOGS_DIR


class AppLogger:
    def __init__(self, name: str = "AI_BOT", log_name: str = "app"):
        self.__logger = colorlog.getLogger(name)
        self.__logger.setLevel(logging.DEBUG)

        self._log_dir = LOGS_DIR / log_name
        self._log_dir.mkdir(parents=True, exist_ok=True)

        self.__current_date = None
        self.__file_handler = None

        color_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]",
            reset=True,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(color_formatter)
        self.__logger.addHandler(console_handler)

        self.__file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s [line:%(lineno)d]'
        )

        self._update_file_handler()

        for noisy in ["asyncio", "aiogram", "pyrofork", "pyrogram", "asyncpg", "googleapiclient"]:
            logging.getLogger(noisy).setLevel(logging.WARNING)

    def _update_file_handler(self):
        """File rotation"""
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self.__current_date:
            if self.__file_handler is not None:
                self.__logger.removeHandler(self.__file_handler)
                self.__file_handler.close()

            filename = self._log_dir / f"{today}.log"
            self.__file_handler = logging.FileHandler(filename, encoding='utf-8')
            self.__file_handler.setFormatter(self.__file_formatter)
            self.__logger.addHandler(self.__file_handler)

            self.__current_date = today

    # --- Public wrapper methods ---

    def info(self, msg: str, *args, **kwargs) -> None:
        """Standard method logger.info() but with the file rotation"""
        self._update_file_handler()
        self.__logger.info(msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs) -> None:
        """Standard method logger.debug() but with the file rotation"""
        self._update_file_handler()
        self.__logger.debug(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        """Standard method logger.warning() but with the file rotation"""
        self._update_file_handler()
        self.__logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        """Standard method logger.error() but with the file rotation"""
        self._update_file_handler()
        self.__logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        """Standard method logger.critical() but with the file rotation"""
        self._update_file_handler()
        self.__logger.critical(msg, *args, **kwargs)


    # --- Custom methods ---

    def log_db_info(self, msg: str) -> None:
        self.info(f"💾 DB INFO: {msg}")

    def log_db_debug(self, msg: str) -> None:
        self.debug(f"💾 DB DEBUG: {msg}")

    def log_db_error(self, query_name: str, err: Exception) -> None:
        self.error(f"💾 DB ERROR in [{query_name}]: {err}", exc_info=True)

    def log_db_critical(self, err: Exception) -> None:
        self.critical(f"💾🔴 DB CRITICAL ERROR: {err}.", exc_info=True)

    def log_middleware_error(self, err: Exception) -> None:
        self.error(f"📨 MIDDLEWARE ERROR: {err}")

    def log_handler_error(self, handler_name: str, err: Exception) -> None:
        self.error(f"🤖 ERROR IN {handler_name}: {err}")


# --- Import only these objects ---
bot_logger = AppLogger(name="ai-bot", log_name="bot")
db_logger = AppLogger(name="db", log_name="database")
