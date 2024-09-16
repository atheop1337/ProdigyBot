from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ChatAction
from modules.libraries.dbms import Database
from modules.libraries.utils import const, _States, _Kbs
from datetime import datetime
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

    class BaseHandler:
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

    class AllProjectsHandler(BaseHandler):
        async def _handle_message(
            self, message: types.Message, state: FSMContext, state_name
        ):
            projects = await self._parent._db.fetch_projects(self._parent._user_id)

            logging.info(
                f"User with id {self._parent._user_id} and name {self._parent._user_name} fetched projects via command"
            )

            if projects:
                projects_list = []
                for project in projects:
                    tasks = await self._parent._db.fetch_tasks(project["id"])
                    if tasks:
                        task_list = []
                        for task in tasks:
                            subtasks = await self._parent._db.fetch_subtasks(
                                project["id"]
                            )
                            if subtasks:
                                subtask_list = "\n".join(
                                    f"Subtask ID: {subtask['id']}, Name: {subtask['name']}, Status: {subtask['status']}"
                                    for subtask in subtasks
                                )
                            else:
                                subtask_list = "\tNo subtasks for this task."

                            task_list.append(
                                f"Task ID: {task['id']}, Name: {task['name']}, "
                                f"Description: {task['description']}, Deadline: {task['deadline']}, "
                                f"Priority: {task['priority']}, Status: {task['status']}\nSubtasks:\n{subtask_list}"
                            )
                        task_list = "\n".join(task_list)
                    else:
                        task_list = "No tasks for this project."

                    projects_list.append(
                        f"Project ID: {project['id']}, Name: {project['name']}, Description: {project['description']}\nTasks:\n{task_list}"
                    )

                response_message = f"Here are your projects:\n\n" + "\n\n".join(
                    projects_list
                )
            else:
                response_message = "You have no projects."

            await message.answer(response_message)

        async def _handle_callback_query(
            self, callback_query: types.CallbackQuery, state: FSMContext, state_name
        ):
            projects = await self._parent._db.fetch_projects(self._parent._user_id)

            if projects:
                projects_list = []
                for project in projects:
                    tasks = await self._parent._db.fetch_tasks(project["id"])
                    logging.info(
                        f"Fetched tasks for project {project['id']} with name '{project['name']}': {tasks}"
                    )
                    if tasks:
                        task_list = []
                        for task in tasks:
                            subtasks = await self._parent._db.fetch_subtasks(
                                project["id"]
                            )
                            if subtasks:
                                subtask_list = "\n".join(
                                    f"\tSubtask ID: {subtask['id']}, Name: {subtask['name']}"
                                    for subtask in subtasks
                                )
                            else:
                                subtask_list = "\tNo subtasks for this task."

                            task_list.append(
                                f"Task ID: {task['id']}, Name: {task['name']}, "
                                f"Description: {task['description']}, Deadline: {task['deadline']}, "
                                f"Priority: {task['priority']}, Status: {task['status']}\nSubtasks:\n{subtask_list}"
                            )
                        task_list = "\n".join(task_list)
                    else:
                        task_list = "No tasks for this project."

                    projects_list.append(
                        f"Project ID: {project['id']}, Name: {project['name']}, Description: {project['description']}\nTasks:\n{task_list}"
                    )

                response_message = f"Here are your projects:\n\n" + "\n\n".join(
                    projects_list
                )
            else:
                response_message = "You have no projects."

            await callback_query.message.answer(response_message)

    class NewProjectHandler(BaseHandler):
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

    class EditProjectHandler(BaseHandler):
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

    class DeleteProjectHandler(BaseHandler):
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

    class NewTaskHandler(BaseHandler):
        async def _handle_message(
            self, message: types.Message, state: FSMContext, state_name
        ):
            projects = await self._parent._db.fetch_projects(self._parent._user_id)
            if not projects:
                await message.answer(
                    "У вас нет проектов, в которых можно создать таск."
                )
                logging.info(
                    f"User {self._parent._user_id} has no projects for task creation."
                )
                await state.clear()
                return

            await state.update_data(projects=projects)

            if state_name is None:
                logging.info(
                    f"User {self._parent._user_id} started creating a new task."
                )
                await message.answer(text="Введите ID проекта.")
                await state.set_state(_States.NewTask.project_id)
            elif state_name == _States.NewTask.project_id:
                await self._handle_project_id(message, state)
            elif state_name == _States.NewTask.task_name:
                await self._handle_task_name(message, state)
            elif state_name == _States.NewTask.task_description:
                await self._handle_task_description(message, state)
            elif state_name == _States.NewTask.deadline:
                await self._handle_deadline(message, state)
            elif state_name == _States.NewTask.priority:
                await self._handle_priority(message, state)

        async def _handle_callback_query(
            self, callback_query: types.CallbackQuery, state: FSMContext, state_name
        ):
            projects = await self._parent._db.fetch_projects(self._parent._user_id)

            if not projects:
                await message.answer("У вас нет проектов, в которых можно создать таск")
                logging.info(
                    f"User {self._parent._user_id} has no projects for task creation."
                )
                await state.clear()
                return

            await state.update_data(projects=projects)

            if state_name is None:
                logging.info(
                    f"User with id {self._parent._user_id} started creating new task via button"
                )
                await callback_query.message.answer(text="Введите ID проекта")
                await state.set_state(_States.NewTask.project_id)
            elif state_name == _States.NewTask.project_id:
                await self._handle_project_id(callback_query.message, state)
            elif state_name == _States.NewTask.task_name:
                await self._handle_task_name(callback_query.message, state)
            elif state_name == _States.NewTast.task_description:
                await self._handle_task_description(callback_query.message, state)
            elif state_name == _States.NewTask.deadline:
                await self._handle_deadline(callback_query.message, state)
            elif state_name == _States.NewTask.priority:
                await self._handle_priority(callback_query.message, state)

        async def _handle_project_id(self, message: types.Message, state: FSMContext):
            project_id = message.text
            try:
                project_id = int(project_id)
            except ValueError:
                await message.answer("ID проекта должен быть числом.")
                logging.warning(
                    f"User {self._parent._user_id} entered an invalid project ID: {project_id}."
                )
                await state.clear()
                return

            projects = await self._parent._db.fetch_projects(self._parent._user_id)

            project = next(
                (proj for proj in projects if proj["id"] == project_id), None
            )
            if project is None:
                await message.answer(
                    f"Проект с ID {project_id} не найден или не принадлежит вам."
                )
                logging.warning(
                    f"User {self._parent._user_id} attempted to select an invalid project ID: {project_id}."
                )
                await state.clear()
                return

            logging.info(
                f"User {self._parent._user_id} selected project with ID {project_id} for task creation."
            )
            await state.update_data(project_id=project_id)
            await message.answer(
                f"Вы выбрали проект: {project['name']}. Введите название таска."
            )
            await state.set_state(_States.NewTask.task_name)

        async def _handle_task_name(self, message: types.Message, state: FSMContext):
            task_name = message.text
            data = await state.get_data()
            project_id = data.get("project_id")
            logging.info(
                f"User {self._parent._user_id} entered task name for project {project_id}: {task_name}."
            )
            await state.update_data(task_name=task_name)
            await message.answer("Введите описание таска.")
            await state.set_state(_States.NewTask.task_description)

        async def _handle_task_description(
            self, message: types.Message, state: FSMContext
        ):
            task_description = message.text
            logging.info(f"User {self._parent._user_id} entered task description.")
            await state.update_data(task_description=task_description)
            await message.answer("Введите срок выполнения таска в формате DD.MM.YYYY.")
            await state.set_state(_States.NewTask.deadline)

        async def _handle_deadline(self, message: types.Message, state: FSMContext):
            deadline = message.text
            try:
                datetime.strptime(deadline, "%d.%m.%Y")
            except ValueError:
                await message.answer("Неверный формат даты. Пример: 31.12.2022.")
                logging.warning(
                    f"User {self._parent._user_id} entered an invalid deadline format: {deadline}."
                )
                await state.clear()
                return
            logging.info(f"User {self._parent._user_id} entered deadline: {deadline}.")
            await state.update_data(deadline=deadline)
            await message.answer("Выберите приоритет таска (1, 2, 3, 4, 5).")
            await state.set_state(_States.NewTask.priority)

        async def _handle_priority(self, message: types.Message, state: FSMContext):
            priority = message.text
            try:
                priority = int(priority)
            except ValueError:
                await message.answer("Приоритет таска должен быть числом.")
                logging.warning(
                    f"User {self._parent._user_id} entered a non-numeric priority: {priority}."
                )
                await state.clear()
                return

            if priority not in [1, 2, 3, 4, 5]:
                await message.answer("Приоритет таска должен быть числом от 1 до 5.")
                logging.warning(
                    f"User {self._parent._user_id} entered an invalid priority: {priority}."
                )
                await state.clear()
                return

            data = await state.get_data()
            project_id = data.get("project_id")
            task_name = data.get("task_name")
            task_description = data.get("task_description")
            deadline = data.get("deadline")

            logging.info(
                f"User {self._parent._user_id} created a task with priority {priority} for project {project_id}."
            )
            _check = await self._parent._db.new_task(
                self._parent._user_id,
                project_id,
                task_name,
                task_description,
                deadline,
                priority,
            )

            if _check:
                _final_message = "Таск успешно создан. Проверьте командой /tasks."
                logging.info(f"Task successfully created for project {project_id}.")
            else:
                _final_message = (
                    "Что-то пошло не так во время создания таска. Попробуйте позже."
                )
                logging.error(f"Failed to create task for project {project_id}.")

            await message.answer(_final_message)
            await state.clear()

    class EditTaskHandler(BaseHandler):
        async def _handle_message(
            self, message: types.Message, state: FSMContext, state_name
        ):
            tasks = await self._parent._db.user_has_tasks(self._parent._user_id)
            if not tasks:
                await message.answer("У вас нет тасков для изменения.")
                await state.clear()
                return

            if state_name is None:
                logging.info(
                    f"User with id {self._parent._user_id} and name {self._parent._user_name} started editing task via command"
                )
                await message.answer(text="Введите ID таска, который хотите изменить")
                await state.set_state(_States.EditTask.task_id)

            elif state_name == _States.EditTask.task_id:
                await self._handle_task_id(message, state)
            elif state_name == _States.EditTask.progress:
                await self._handle_task_progress(message, state)

        async def _handle_callback_query(
            self, callback_query: types.CallbackQuery, state: FSMContext, state_name
        ):
            tasks = await self._parent._db.user_has_tasks(self._parent._user_id)
            if not tasks:
                await callback_query.message.answer("У вас нет тасков для изменения.")
                await state.clear()
                return

            if state_name is None:
                logging.info(
                    f"User with id {self._parent._user_id} and name {self._parent._user_name} started editing task via callback query"
                )
                await callback_query.message.answer(
                    text="Введите ID таска, который хотите изменить"
                )
                await state.set_state(_States.EditTask.task_id)

            elif state_name == _States.EditTask.task_id:
                await self._handle_task_id(callback_query.message, state)
            elif state_name == _States.EditTask.progress:
                await self._handle_task_progress(callback_query.message, state)

        async def _handle_task_id(self, message: types.Message, state: FSMContext):
            task_id = message.text
            try:
                task_id = int(task_id)
            except ValueError:
                await message.answer("ID таска должен быть числом.")
                await state.clear()
                return

            task = await self._parent._db.fetch_task(task_id)
            if not task:
                await message.answer(
                    "Таска с таким ID не существует. Попробуйте еще раз."
                )
                await state.clear()
                return

            await state.update_data(task_id=task_id)
            await message.answer("Введи прогресс (0 - в прогрессе, 1 - завершено)")
            await state.set_state(_States.EditTask.progress)

        async def _handle_task_progress(
            self, message: types.Message, state: FSMContext
        ):
            progress = message.text
            try:
                progress = int(progress)
            except ValueError:
                await message.answer("Прогресс должен быть числом.")
                await state.clear()
                return

            if progress not in [0, 1]:
                await message.answer("Прогресс может быть только 0 или 1.")
                await state.clear()
                return

            data = await state.get_data()
            task_id = data.get("task_id")

            success = await self._parent._db.edit_task(task_id, progress)
            if success:
                _final_message = "Таск успешно изменен. Проверьте командой /projects."
                logging.info(f"Task successfully edited with ID {task_id}.")
            else:
                _final_message = "Ошибка при изменении таска. Попробуйте позже."
                logging.error(f"Failed to edit task with ID {task_id}.")

            await message.answer(_final_message)
            await state.clear()

    class DeleteTaskHandler(BaseHandler):
        async def _handle_message(
            self, message: types.Message, state: FSMContext, state_name
        ):
            tasks = await self._parent._db.user_has_tasks(self._parent._user_id)
            if not tasks:
                await message.answer("У вас нет тасков для удаления.")
                await state.clear()
                return

            if state_name is None:
                logging.info(
                    f"User with id {self._parent._user_id} and name {self._parent._user_name} started deleting task via command"
                )
                await message.answer(text="Введите ID таска, который хотите удалить")
                await state.set_state(_States.DeleteTask.task_id)

            elif state_name == _States.DeleteTask.task_id:
                await self._handle_task_id(message, state)

        async def _handle_callback_query(
            self, callback_query: types.CallbackQuery, state: FSMContext, state_name
        ):
            tasks = await self._parent._db.user_has_tasks(self._parent._user_id)
            if not tasks:
                await message.answer("У вас нет тасков для удаления.")
                await state.clear()
                return

            if state_name is None:
                logging.info(
                    f"User with id {self._parent._user_id} and name {self._parent._user_name} started deleting task via button"
                )
                await message.answer(text="Введите ID таска, который хотите удалить")
                await state.set_state(_States.DeleteTask.task_id)

            elif state_name == _States.DeleteTask.task_id:
                await self._handle_task_id(message, state)

        async def _handle_task_id(self, message: types.Message, state: FSMContext):
            task_id = message.text
            try:
                task_id = int(task_id)
            except ValueError:
                await message.answer("ID таска должен быть числом.")
                await state.clear()
                return

            task = await self._parent._db.fetch_task(task_id)
            if not task:
                await message.answer(
                    "Таска с таким ID не существует. Попробуйте еще раз."
                )
                await state.clear()
                return

            _check = await self._parent._db.remove_task(task_id)

            if _check:
                _final_message = "Таск успешно удален. Проверьте командой /projects."
                logging.info(f"Task successfully deleted with ID {task_id}.")
            else:
                _final_message = "Ошибка при удалении таска. Попробуйте позже."
                logging.error(f"Failed to delete task with ID {task_id}.")

            await message.answer(_final_message)
            await state.clear()

    class NewSubTaskHandler(BaseHandler):
        async def _handle_message(
            self, message: types.Message, state: FSMContext, state_name
        ):
            projects = await self._parent._db.fetch_projects(self._parent._user_id)
            if not projects:
                await message.answer("У вас нет проектов для создания подзадачи.")
                await state.clear()
                return

            tasks = await self._parent._db.fetch_tasks(projects[0]["id"])
            if not tasks:
                await message.answer("У вас нет тасков для создания подзадачи.")
                await state.clear()
                return

            if state_name is None:
                logging.info(
                    f"User with id {self._parent._user_id} and name {self._parent._user_name} started creating new subtask via command"
                )
                await message.answer(text="Выберите айди таска для создания подзадачи")
                await state.set_state(_States.NewSubTask.task_id)
            elif state_name == _States.NewSubTask.task_id:
                await self._handle_task_id(message, state)
            elif state_name == _States.NewSubTask.subtask_name:
                await self._handle_subtask_name(message, state)

        async def _handle_callback_query(
            self, callback_query: types.CallbackQuery, state: FSMContext, state_name
        ):
            projects = await self._parent._db.fetch_projects(self._parent._user_id)
            if not projects:
                await callback_query.message.answer(
                    "У вас нет проектов для создания подзадачи."
                )
                await state.clear()
                return

            tasks = await self._parent.db.fetch_tasks(projects[0]["id"])
            if not tasks:
                await callback_query.message.answer(
                    "У вас нет тасков для создания подзадачи."
                )
                await state.clear()
                return

            if state_name is None:
                logging.info(
                    f"User with id {self._parent._user_id} and name {self._parent._user_name} started creating new subtask via command"
                )
                await message.answer(text="Выберите айди таска для создания подзадачи")
                await state.set_state(_States.NewSubTask.task_id)
            elif state_name == _States.NewSubTask.task_id:
                await self._handle_task_id(message, state)
            elif state_name == _States.NewSubTask.subtask_name:
                await self._handle_subtask_name(message, state)

        async def _handle_task_id(self, message: types.Message, state: FSMContext):
            task_id = message.text
            try:
                task_id = int(task_id)
            except ValueError:
                await message.answer("ID таска должен быть числом.")
                await state.clear()
                return

            _exist = self._parent._db.fetch_task(task_id)
            if not _exist:
                await message.answer(
                    "Таска с таким ID не существует. Попробуйте еще раз."
                )
                await state.clear()
                return

            await state.update_data(task_id=task_id)
            await message.answer("Выберите название подзадачи")
            await state.set_state(_States.NewSubTask.subtask_name)

        async def _handle_subtask_name(self, message: types.Message, state: FSMContext):
            subtask_name = message.text
            data = await state.get_data()
            task_id = data.get("task_id")

            _check = await self._parent._db.add_subtask(task_id, subtask_name)

            if _check:
                _final_message = (
                    "Подзадача успешно создана. Проверьте командой /projects."
                )
                logging.info(f"Subtask successfully added with ID {task_id}.")
            else:
                _final_message = "Ошибка при создании подзадачи. Попробуйте позже."
                logging.error(f"Failed to add subtask with ID {task_id}.")

            await message.answer(_final_message)
            await state.clear()

    class EditSubTaskHandler(BaseHandler):
        async def _handle_message(
            self, message: types.Message, state: FSMContext, state_name
        ):
            subtasks = await self._parent._db.user_has_subtasks(self._parent._user_id)

            if not subtasks:
                await message.answer("У вас нет подзадач для редактирования.")
                await state.clear()
                return

            if state_name is None:
                logging.info(
                    f"User with id {self._parent._user_id} and name {self._parent._user_name} started editing subtask via command"
                )
                await message.answer(
                    text="Выберите ID подзадачи для редактирования (установки как выполненное)"
                )
                await state.set_state(_States.EditSubTask.subtask_id)

            elif state_name == _States.EditSubTask.subtask_id:
                await self._handle_subtask_id(message, state)

        async def _handle_callback_query(
            self, callback_query: types.CallbackQuery, state: FSMContext, state_name
        ):
            subtasks = await self._parent._db.user_has_subtasks(self._parent._user_id)

            if not subtasks:
                await message.answer("У вас нет подзадач для редактирования.")
                await state.clear()
                return

            if state_name is None:
                logging.info(
                    f"User with id {self._parent._user_id} and name {self._parent._user_name} started editing subtask via command"
                )
                await message.answer(
                    text="Выберите ID подзадачи для редактирования (установки как выполненное)"
                )
                await state.set_state(_States.EditSubTask.subtask_id)

            elif state_name == _States.EditSubTask.subtask_id:
                await self._handle_subtask_id(message, state)

        async def _handle_subtask_id(self, message: types.Message, state: FSMContext):
            subtask_id = message.text
            try:
                subtask_id = int(subtask_id)
            except ValueError:
                await message.answer("ID подзадачи должен быть числом.")
                await state.clear()
                return

            _exist = await self._parent._db.fetch_subtask(subtask_id)

            if not _exist:
                await message.answer(
                    "Подзадача с таким ID не существует. Попробуйте еще раз."
                )
                await state.clear()
                return

            _check = await self._parent._db.edit_subtask(subtask_id)

            if _check:
                _final_message = (
                    "Статус подзадачи успешно изменен. Проверьте командой /projects."
                )
                logging.info(
                    f"Subtask status successfully updated with ID {subtask_id}."
                )
            else:
                _final_message = (
                    "Ошибка при изменении статуса подзадачи. Попробуйте позже."
                )
                logging.error(f"Failed to update subtask status with ID {subtask_id}.")

            await message.answer(_final_message)
            await state.clear()

    class DeleteSubTaskHandler(BaseHandler):
        async def _handle_message(
            self, message: types.Message, state: FSMContext, state_name
        ):
            subtasks = await self._parent._db.user_has_subtasks(self._parent._user_id)

            if not subtasks:
                await message.answer("У вас нет подзадач для удаления.")
                await state.clear()
                return

            if state_name is None:
                logging.info(
                    f"User with id {self._parent._user_id} and name {self._parent._user_name} started deleting subtask via command"
                )
                await message.answer(text="Выберите ID подзадачи для удаления")
                await state.set_state(_States.DeleteSubTask.subtask_id)

            elif state_name == _States.DeleteSubTask.subtask_id:
                await self._handle_subtask_id(message, state)

        async def _handle_callback_query(
            self, callback_query: types.CallbackQuery, state: FSMContext, state_name
        ):
            subtasks = await self._parent._db.user_has_subtasks(self._parent._user_id)

            if not subtasks:
                await message.answer("У вас нет подзадач для удаления.")
                await state.clear()
                return

            if state_name is None:
                logging.info(
                    f"User with id {self._parent._user_id} and name {self._parent._user_name} started deleting subtask via button"
                )
                await message.answer(text="Выберите ID подзадачи для удаления")
                await state.set_state(_States.EditSubTask.subtask_id)

            elif state_name == _States.EditSubTask.subtask_id:
                await self._handle_subtask_id(message, state)

        async def _handle_subtask_id(
            self, message: types.Message, state: FSMContext
        ):
            subtask_id = message.text

            try:
                subtask_id = int(subtask_id)
            except ValueError:
                await message.answer("ID подзадачи должен быть числом.")
                await state.clear()
                return
                
            _exist = await self._parent._db.fetch_subtask(subtask_id)

            if not _exist:
                await message.answer(
                    "Подзадача с таким ID не существует. Попробуйте еще раз."
                )
                await state.clear()
                return

            _check = await self._parent._db.delete_subtask(subtask_id)

            if _check:
                _final_message = (
                    "Подзадача успешно удалена. Проверьте командой /projects."
                )
                logging.info(f"Subtask successfully deleted with ID {subtask_id}.")
            else:
                _final_message = "Ошибка при удалении подзадачи. Попробуйте позже."
                logging.error(f"Failed to delete subtask with ID {subtask_id}.")

            await message.answer(_final_message)
            await state.clear()