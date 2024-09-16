from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ChatAction
from modules.libraries.dbms import Database
from modules.libraries.utils import const, _States, _Kbs
from typing import Union
import logging


class Handlers:
    def __init__(self, db: str):
        self._db = Database(db)
        self._user_id = None
        self._user_name = None

    async def get_info(self, type: Union[types.Message, types.CallbackQuery]):
        if isinstance(type, (types.Message, types.CallbackQuery)):
            self._user_id = type.from_user.id
            self._user_name = type.from_user.username
        else:
            raise ValueError("Unsupported type provided")

    class StartHandler:
        def __init__(self, parent):
            self._parent = parent

        async def handle_start(self, message: types.Message):
            await self._parent.get_info(message)

            logging.info(
                f"Successfully started with user ID {self._parent._user_id} and name {self._parent._user_name}"
            )

            await self._parent._db.add_user(
                self._parent._user_id, self._parent._user_name
            )

            await message.answer(
                f"Hello, {self._parent._user_name}!\n\nThis is a project management bot with reminders and task tracker.\n\n"
            )

    class BaseProjectHandler:
        def __init__(self, parent):
            self._parent = parent

        async def handle(
            self, type: Union[types.Message, types.CallbackQuery], state: FSMContext
        ):
            await self._parent.get_info(type)
            state_name = await state.get_state()

            if isinstance(type, types.Message):
                await self._handle_message(type, state, state_name)
            elif isinstance(type, types.CallbackQuery):
                await self._handle_callback_query(type, state, state_name)
            else:
                logging.warning("Unsupported type provided")

        async def _handle_message(
            self, message: types.Message, state: FSMContext, state_name
        ):
            raise NotImplementedError

        async def _handle_callback_query(
            self, callback_query: types.CallbackQuery, state: FSMContext, state_name
        ):
            raise NotImplementedError

    class AllProjectsHandler(BaseProjectHandler):

        async def _handle_message(
            self, message: types.Message, state: FSMContext, state_name
        ):
            user_id = message.from_user.id
            projects = await self._parent._db.fetch_projects(user_id)

            logging.info(
                f"User with id {self._parent._user_id} and name {self._parent._user_name} fetched projects via command"
            )

            if projects:
                projects_list = "\n".join(
                    f"Project ID: {project['id']}, Name: {project['name']}, Description: {project['description']}"
                    for project in projects
                )
                response_message = f"Here are your projects:\n{projects_list}"
            else:
                response_message = "You have no projects."

            await message.answer(response_message)

        async def _handle_callback_query(
            self, callback_query: types.CallbackQuery, state: FSMContext, state_name
        ):
            user_id = callback_query.from_user.id
            projects = await self._parent._db.fetch_projects(user_id)

            logging.info(
                f"User with id {self._parent._user_id} and name {self._parent._user_name} fetched projects via button"
            )

            if projects:
                projects_list = "\n".join(
                    f"Project ID: {project['id']}, Name: {project['name']}"
                    for project in projects
                )
                response_message = f"Here are your projects:\n{projects_list}"
            else:
                response_message = "You have no projects."

            await callback_query.message.answer(response_message)

    class NewProjectHandler(BaseProjectHandler):
        async def _handle_message(
            self, message: types.Message, state: FSMContext, state_name
        ):
            if state_name is None:
                logging.info(
                    f"User with id {self._parent._user_id} and name {self._parent._user_name} started to create a new project via command"
                )
                await message.answer(text="Введите имя проекта")
                await state.set_state(_States.NewProject.project_name)
            elif state_name == _States.NewProject.project_name:
                await self._handle_project_name(message, state)
            elif state_name == _States.NewProject.project_description:
                await self._handle_project_description(message, state)

        async def _handle_callback_query(
            self, callback_query: types.CallbackQuery, state: FSMContext, state_name
        ):
            if state_name is None:
                logging.info(
                    f"User with id {self._parent._user_id} and name {self._parent._user_name} started to create a new project via button"
                )
                await callback_query.message.answer(text="Введите имя проекта")
                await state.set_state(_States.NewProject.project_name)
            elif state_name == _States.NewProject.project_name:
                await self._handle_project_name(callback_query.message, state)
            elif state_name == _States.NewProject.project_description:
                await self._handle_project_description(callback_query.message, state)

        async def _handle_project_name(self, message: types.Message, state: FSMContext):
            project_name = message.text
            logging.info(
                f"User with id {self._parent._user_id} chose a name for their project: {project_name}"
            )
            await state.update_data(project_name=project_name)
            await message.answer(text="Введите описание проекта")
            await state.set_state(_States.NewProject.project_description)

        async def _handle_project_description(
            self, message: types.Message, state: FSMContext
        ):
            data = await state.get_data()
            project_name = data.get("project_name")
            project_description = message.text
            logging.info(
                f"User with id {self._parent._user_id} provided a description for their project {project_name}"
            )
            _new_project = await self._parent._db.new_project(
                self._parent._user_id, project_name, project_description
            )

            if _new_project:
                _final_message = "Проект успешно создан"
            else:
                _final_message = (
                    "Что-то пошло не так во время создания проекта. Попробуйте позже"
                )

            await message.answer(text=_final_message)
            await state.clear()

    class EditProjectHandler(BaseProjectHandler):
        async def _handle_message(
            self, message: types.Message, state: FSMContext, state_name
        ):
            if state_name is None:
                logging.info(
                    f"User with id {self._parent._user_id} and name {self._parent._user_name} started editing project via command"
                )
                await message.answer(
                    text="Введите имя проекта, который хотите изменить"
                )
                await state.set_state(_States.EditProject.project_old_name)
            elif state_name == _States.EditProject.project_old_name:
                await self._handle_project_old_name(message, state)
            elif state_name == _States.EditProject.project_new_name:
                await self._handle_project_new_name(message, state)
            elif state_name == _States.EditProject.project_new_description:
                await self._handle_project_new_description(message, state)

        async def _handle_callback_query(
            self, callback_query: types.CallbackQuery, state: FSMContext, state_name
        ):
            if state_name is None:
                logging.info(
                    f"User with id {self._parent._user_id} and name {self._parent._user_name} started editing project via callback"
                )
                await callback_query.message.answer(
                    text="Введите имя проекта, который хотите изменить"
                )
                await state.set_state(_States.EditProject.project_old_name)
            elif state_name == _States.EditProject.project_old_name:
                await self._handle_project_old_name(callback_query.message, state)
            elif state_name == _States.EditProject.project_new_name:
                await self._handle_project_new_name(callback_query.message, state)
            elif state_name == _States.EditProject.project_new_description:
                await self._handle_project_new_description(
                    callback_query.message, state
                )

        async def _handle_project_old_name(
            self, message: types.Message, state: FSMContext
        ):
            project_old_name = message.text
            logging.info(
                f"User with id {self._parent._user_id} chose a project to edit: {project_old_name}"
            )
            await state.update_data(project_old_name=project_old_name)
            await message.answer(text="Введите новое имя проекта")
            await state.set_state(_States.EditProject.project_new_name)

        async def _handle_project_new_name(
            self, message: types.Message, state: FSMContext
        ):
            data = await state.get_data()
            project_old_name = data.get("project_old_name")
            project_new_name = message.text
            logging.info(
                f"User with id {self._parent._user_id} provided a new name for their project {project_old_name} to {project_new_name}"
            )
            await state.update_data(project_new_name=project_new_name)
            await message.answer(text="Введите новое описание проекта")
            await state.set_state(_States.EditProject.project_new_description)

        async def _handle_project_new_description(
            self, message: types.Message, state: FSMContext
        ):
            data = await state.get_data()
            project_old_name = data.get("project_old_name")
            project_new_name = data.get("project_new_name")
            project_new_description = message.text
            logging.info(
                f"User with id {self._parent._user_id} provided a new description for their project {project_old_name} to {project_new_description}"
            )
            _edited_project = await self._parent._db.edit_project(
                self._parent._user_id,
                project_old_name,
                project_new_name,
                project_new_description,
            )
            if _edited_project:
                _final_message = "Проект успешно изменен, проверьте командой /projects"
            else:
                _final_message = (
                    "Что-то пошло не так во время изменения проекта. Попробуйте позже"
                )
            await message.answer(_final_message)
            await state.clear()

    class DeleteProjectHandler(BaseProjectHandler):
        async def _handle_message(
            self, message: types.Message, state: FSMContext, state_name
        ):
            projects = await self._parent._db.fetch_projects(self._parent._user_id)
            if not projects:
                await message.answer("У вас нет проектов для удаления.")
                await state.clear()
                return

            await state.update_data(projects=projects)

            if state_name is None:
                logging.info(
                    f"User with id {self._parent._user_id} and name {self._parent._user_name} started deleting a project via command"
                )
                await message.answer(text="Введите ID проекта, который хотите удалить")
                await state.set_state(_States.DeleteProject.project_id)
            elif state_name == _States.DeleteProject.project_id:
                await self._handle_project_id(message, state)

        async def _handle_callback_query(
            self, callback_query: types.CallbackQuery, state: FSMContext, state_name
        ):
            projects = await self._parent._db.fetch_projects(self._parent._user_id)
            if not projects:
                await callback_query.message.answer("У вас нет проектов для удаления.")
                await state.clear()
                return

            await state.update_data(projects=projects)

            if state_name is None:
                logging.info(
                    f"User with id {self._parent._user_id} started deleting a project via callback"
                )
                await callback_query.message.answer(text="Введите ID проекта")
                await state.set_state(_States.DeleteProject.project_id)
            elif state_name == _States.DeleteProject.project_id:
                await self._handle_project_id(callback_query.message, state)

        async def _handle_project_id(self, message: types.Message, state: FSMContext):
            project_id = message.text
            try:
                project_id = int(project_id)
            except ValueError:
                await message.answer("ID проекта должен быть числом.")
                await state.clear()
                return

            logging.info(
                f"User with id {self._parent._user_id} selected project with ID {project_id} for deletion"
            )

            data = await state.get_data()
            projects = data.get("projects")

            project_to_delete = next(
                (project for project in projects if project["id"] == project_id), None
            )

            if not project_to_delete:
                await message.answer("Проект с таким ID не найден.")
                await state.clear()
                return

            _deleted_project = await self._parent._db.delete_project(project_id)

            if _deleted_project:
                _final_message = "Проект успешно удален. Проверьте командой /projects"
            else:
                _final_message = (
                    "Что-то пошло не так во время удаления проекта. Попробуйте позже."
                )

            await message.answer(_final_message)
            await state.clear()
