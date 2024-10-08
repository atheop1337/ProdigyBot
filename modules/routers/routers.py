from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart, Command
from modules.handlers import (
    start_handler,
    info_handler,
    new_project_handler,
    all_project_handlers,
    edit_project_handler,
    delete_project_handler,
    new_task_handler,
    edit_task_handler,
    delete_task_handler,
    new_subtask_handler,
    edit_subtask_handler,
    delete_subtask_handler,
    share_project_handler,
)
from modules.libraries.utils import _States
from typing import Union

router = Router()


@router.message(CommandStart())
async def start_handler_command(message: types.Message):
    await start_handler.handle_start(message)


@router.callback_query(F.data == "create")
@router.message(Command("new_project"))
@router.message(_States.NewProject.project_name)
@router.message(_States.NewProject.project_description)
async def create_handler(
    type: Union[types.Message, types.CallbackQuery], state: FSMContext
):
    await new_project_handler.handle(type, state)


@router.callback_query(F.data == "edit")
@router.message(Command("edit_project"))
@router.message(_States.EditProject.project_old_name)
@router.message(_States.EditProject.project_new_name)
@router.message(_States.EditProject.project_new_description)
async def edit_handler(
    type: Union[types.Message, types.CallbackQuery], state: FSMContext
):
    await edit_project_handler.handle(type, state)


@router.callback_query(F.data == "delete")
@router.message(Command("delete_project"))
@router.message(_States.DeleteProject.project_id)
async def delete_handler(
    type: Union[types.Message, types.CallbackQuery], state: FSMContext
):
    await delete_project_handler.handle(type, state)


@router.callback_query(F.data == "projects")
@router.message(Command("projects"))
async def projects_handler(
    type: Union[types.Message, types.CallbackQuery], state: FSMContext
):
    await all_project_handlers.handle(type, state)


@router.callback_query(F.data == "create_task")
@router.message(Command("new_task"))
@router.message(_States.NewTask.project_id)
@router.message(_States.NewTask.task_name)
@router.message(_States.NewTask.task_description)
@router.message(_States.NewTask.deadline)
@router.message(_States.NewTask.priority)
async def create_task_handler(
    type: Union[types.Message, types.CallbackQuery], state: FSMContext
):
    await new_task_handler.handle(type, state)


@router.callback_query(F.data == "edit_task")
@router.message(Command("edit_task"))
@router.message(_States.EditTask.task_id)
@router.message(_States.EditTask.progress)
async def edit_task_handler_func(
    type: Union[types.Message, types.CallbackQuery], state: FSMContext
):
    await edit_task_handler.handle(type, state)


@router.callback_query(F.data == "delete_task")
@router.message(Command("delete_task"))
@router.message(_States.DeleteTask.task_id)
async def delete_task_handler_func(
    type: Union[types.Message, types.CallbackQuery], state: FSMContext
):
    await delete_task_handler.handle(type, state)


@router.callback_query(F.data == "new_subtask")
@router.message(Command("new_subtask"))
@router.message(_States.NewSubTask.task_id)
@router.message(_States.NewSubTask.subtask_name)
async def new_subtask_handler_func(
    type: Union[types.Message, types.CallbackQuery], state: FSMContext
):
    await new_subtask_handler.handle(type, state)


@router.callback_query(F.data == "edit_subtask")
@router.message(Command("edit_subtask"))
@router.message(_States.EditSubTask.subtask_id)
async def edit_subtask_handler_func(
    type: Union[types.Message, types.CallbackQuery], state: FSMContext
):
    await edit_subtask_handler.handle(type, state)


@router.callback_query(F.data == "delete_subtask")
@router.message(Command("delete_subtask"))
@router.message(_States.DeleteSubTask.subtask_id)
async def delete_subtask_handler_func(
    type: Union[types.Message, types.CallbackQuery], state: FSMContext
):
    await delete_subtask_handler.handle(type, state)


@router.callback_query(F.data == "share_project")
@router.message(Command("share_project"))
@router.message(_States.ShareProject.project_id)
@router.message(_States.ShareProject.participator_user_id)
async def share_project_handler_func(
    type: Union[types.Message, types.CallbackQuery], state: FSMContext
):
    await share_project_handler.handle(type, state)


@router.message(Command(commands=["help", "info"]))
async def info_handler_func(
    type: Union[types.Message, types.CallbackQuery], state: FSMContext
):
    await info_handler.handle(type, state)
