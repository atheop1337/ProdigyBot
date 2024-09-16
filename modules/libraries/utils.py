import random, string
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from modules.libraries.dbms import Database


class const:
    DATABASE_NAME = "database/prodigy_bot.db"


class _Kbs:

    @staticmethod
    def get_welcome_kb() -> InlineKeyboardMarkup:
        kb = [[InlineKeyboardButton(text="⚖ Create", callback_data="create")]]

        return InlineKeyboardMarkup(inline_keyboard=kb)


class _States:

    class NewProject(StatesGroup):
        project_name = State()
        project_description = State()

    class EditProject(StatesGroup):
        project_old_name = State()
        project_new_name = State()
        project_new_description = State()

    class DeleteProject(StatesGroup):
        project_id = State()
