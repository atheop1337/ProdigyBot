from modules.handlers.handlers import Handlers
from modules.libraries.utils import const

# Main handler
handlers = Handlers(const.DATABASE_NAME)

# Start handler
start_handler = handlers.StartHandler(parent=handlers)

# Project handlers
new_project_handler = handlers.NewProjectHandler(parent=handlers)
edit_project_handler = handlers.EditProjectHandler(parent=handlers)
delete_project_handler = handlers.DeleteProjectHandler(parent=handlers)
all_project_handlers = handlers.AllProjectsHandler(parent=handlers)

# Task handlers
new_task_handler = handlers.NewTaskHandler(parent=handlers)
edit_task_handler = handlers.EditTaskHandler(parent=handlers)
delete_task_handler = handlers.DeleteTaskHandler(parent=handlers)
