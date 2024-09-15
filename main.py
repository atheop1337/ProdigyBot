"""
AUTHOR: github.com/atheop1337 😘
"""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from modules.libraries.dbms import Database
from modules.routers.routers import router as handlers_router
from modules.libraries.utils import const
from datetime import datetime
import asyncio, logging, os

TOKEN_FILE_PATH = r"C:\Everything\tokens\prodigy\TOKEN"


def read_token_from_file(file_path) -> str:
    try:
        with open(file_path, "r") as file:
            token = file.read().strip()
            return token
    except Exception as e:
        raise ValueError(f"Error reading token from file: {e}")


def setup_logging():
    log_dir = ".logs"
    os.makedirs(log_dir, exist_ok=True)

    log_filename = os.path.join(
        log_dir, datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log")
    )

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s]:%(levelname)s:%(funcName)s:%(message)s",
        datefmt="%Y-%m-%d|%H:%M:%S",
        handlers=[logging.FileHandler(log_filename), logging.StreamHandler()],
    )


TOKEN = read_token_from_file(TOKEN_FILE_PATH)
if not TOKEN:
    raise ValueError("No BOT_TOKEN found in the token file. Please check your token.")


async def main() -> None:
    db = Database(const.DATABASE_NAME)
    await db.create_tables()
    dp = Dispatcher()
    dp.include_routers(handlers_router)
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await db.close()


if __name__ == "__main__":
    try:
        setup_logging()
        logging.info(f"Using {'WIN' if os.name == 'nt' else 'UNIX'} base kernel")
        asyncio.run(main())
    except Exception as e:
        logging.exception("An error occurred")
