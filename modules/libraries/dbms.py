import aiosqlite
import logging
from typing import Union


class Database:
    def __init__(self, db: str):
        self.db_path = db

    async def create_tables(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.cursor() as cursor:
                await cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER UNIQUE,
                        user_name TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        notifications BOOLEAN DEFAULT TRUE
                    )
                    """
                )

                await cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        name TEXT NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                    """
                )

                await cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER,
                        name TEXT NOT NULL,
                        description TEXT,
                        deadline TIMESTAMP,
                        priority INTEGER,
                        status TEXT CHECK(status IN ('in progress', 'completed')) DEFAULT 'in progress',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (project_id) REFERENCES projects (id)
                    )
                    """
                )

                await cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS subtasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id INTEGER,
                        name TEXT NOT NULL,
                        status TEXT CHECK(status IN ('in progress', 'completed')) DEFAULT 'in progress',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (task_id) REFERENCES tasks (id)
                    )
                    """
                )

                await cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS shared_projects (
                        project_id INTEGER,
                        user_id INTEGER,
                        PRIMARY KEY (project_id, user_id),
                        FOREIGN KEY (project_id) REFERENCES projects (id),
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                    """
                )

                logging.info("Successfully created tables")
                await db.commit()

    async def add_user(self, user_id: int, user_name: str) -> bool:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.cursor() as cursor:
                    await cursor.execute(
                        "INSERT INTO users (user_id, user_name) VALUES (?,?)",
                        (user_id, user_name),
                    )
                    await db.commit()
                    logging.info(f"Added user with ID {user_id} and name {user_name}")
                    return True
        except aiosqlite.IntegrityError:
            logging.info(
                f"User with name ID {user_id} and name {user_name} already exists"
            )
            return True
        except Exception as e:
            logging.error(f"Error occurred while adding user: {e}")
            return False

    async def new_project(self, user_id: int, name: str, desc: str) -> bool:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.cursor() as cursor:
                    await cursor.execute(
                        "INSERT INTO projects (user_id, name, description) VALUES (?,?,?)",
                        (user_id, name, desc),
                    )
                    await db.commit()
                    logging.info(
                        f"User with id {user_id} successfully created new project with name {name}"
                    )
                    return True
        except Exception as e:
            logging.error(f"Error occurred while adding project: {e}")
            return False

    async def edit_project(
        self, user_id: int, old_name: str, new_name: str, new_desc: str
    ) -> bool:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE projects SET name=?, description=? WHERE user_id=? AND name=?",
                        (new_name, new_desc, user_id, old_name),
                    )
                    await db.commit()
                    logging.info(
                        f"User with id {user_id} successfully edited project with name {old_name} to {new_name}"
                    )
                    return True
        except Exception as e:
            logging.error(f"Error occurred while editing project: {e}")
            return False

    async def delete_project(self, project_id: int) -> bool:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.cursor() as cursor:
                    await cursor.execute(
                        "DELETE FROM projects WHERE id =?", (project_id,)
                    )
                    await db.commit()
                    logging.info(f"Deleted project with id {project_id}")
                    return True
        except Exception as e:
            logging.error(f"Error occurred while deleting project: {e}")
            return False

    async def fetch_projects(self, user_id: int) -> list:
        projects = []
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.cursor() as cursor:
                    await cursor.execute(
                        "SELECT id, name, description FROM projects WHERE user_id = ?",
                        (user_id,),
                    )
                    rows = await cursor.fetchall()
                    for row in rows:
                        projects.append(
                            {"id": row[0], "name": row[1], "description": row[2]}
                        )
                    logging.info(f"Fetched all projects for user with id {user_id}")
        except Exception as e:
            logging.error(f"Error occurred while fetching projects: {e}")
        return projects

    async def new_task(
        self,
        user_id: int,
        project_id: int,
        task_name: str,
        task_description: str,
        task_deadline: any,
        priority: int,
    ) -> bool:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.cursor() as cursor:
                    await cursor.execute(
                        "INSERT INTO tasks (project_id, name, description, deadline, priority) VALUES (?,?,?,?,?)",
                        (
                            project_id,
                            task_name,
                            task_description,
                            task_deadline,
                            priority,
                        ),
                    )
                    await db.commit()
                    logging.info(
                        f"User with id {user_id} successfully created new task with name {task_name} for project with ID {project_id}"
                    )
                    return True
        except Exception as e:
            logging.error(f"Error occurred while adding task: {e}")
            return False

    async def fetch_tasks(self, project_id: int) -> list:
        tasks = []
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.cursor() as cursor:
                    await cursor.execute(
                        "SELECT id, name, description, deadline, priority, status FROM tasks WHERE project_id =?",
                        (project_id,),
                    )
                    rows = await cursor.fetchall()
                    for row in rows:
                        tasks.append(
                            {
                                "id": row[0],
                                "name": row[1],
                                "description": row[2],
                                "deadline": row[3],
                                "priority": row[4],
                                "status": row[5],
                            }
                        )
                    logging.info(f"Fetched all tasks for project with id {project_id}")
        except Exception as e:
            logging.error(f"Error occurred while fetching tasks: {e}")
        return tasks

    async def fetch_task(self, task_id: int) -> dict:
        task = None
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.cursor() as cursor:
                    await cursor.execute(
                        "SELECT id, name, description, deadline, priority, status FROM tasks WHERE id = ?",
                        (task_id,),
                    )
                    row = await cursor.fetchone()
                    if row:
                        task = {
                            "id": row[0],
                            "name": row[1],
                            "description": row[2],
                            "deadline": row[3],
                            "priority": row[4],
                            "status": row[5],
                        }
                        logging.info(f"Fetched task with id {task_id}")
                    else:
                        logging.info(f"Task with id {task_id} not found.")
        except Exception as e:
            logging.error(f"Error occurred while fetching task with id {task_id}: {e}")

        return task

    async def user_has_tasks(self, user_id: int) -> bool:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.cursor() as cursor:
                    await cursor.execute(
                        "SELECT id FROM projects WHERE user_id = ?", (user_id,)
                    )
                    projects = await cursor.fetchall()

                    if not projects:
                        logging.info(f"User with id {user_id} has no projects.")
                        return False

                    for project in projects:
                        project_id = project[0]
                        await cursor.execute(
                            "SELECT COUNT(*) FROM tasks WHERE project_id = ?",
                            (project_id,),
                        )
                        task_count = await cursor.fetchone()

                        if task_count and task_count[0] > 0:
                            logging.info(
                                f"User with id {user_id} has tasks in project {project_id}."
                            )
                            return True

                    logging.info(f"User with id {user_id} has no tasks in any project.")
                    return False
        except Exception as e:
            logging.error(f"Error occurred while checking user tasks: {e}")
            return False

    async def edit_task(self, task_id: int, progress: int) -> bool:
        if progress == 1:
            progress = "completed"
        elif progress == 0:
            progress = "in progress"
        else:
            logging.error(f"Invalid progress value: {progress}")
            return False
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE tasks SET status=? WHERE id =?",
                        (progress, task_id),
                    )
                    await db.commit()
                    logging.info(f"Updated task with id {task_id} to status {progress}")
                    return True
        except Exception as e:
            logging.error(f"Error occurred while editing task: {e}")
            return False

    async def remove_task(self, task_id: int) -> bool:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.cursor() as cursor:
                    await cursor.execute("DELETE FROM tasks WHERE id =?", (task_id,))
                    await db.commit()
                    logging.info(f"Deleted task with id {task_id}")
                    return True
        except Exception as e:
            logging.error(f"Error occurred while deleting task: {e}")
            return False

    async def close(self) -> None:
        if self.conn:
            await self.conn.close()
