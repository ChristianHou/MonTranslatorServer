# task_manager.py
from enum import Enum


# 定义任务状态枚举类
class TaskStatus(str, Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# 任务管理器类
class TaskManager:
    def __init__(self):
        self.tasks = {}

    def add_task(self, task_id: str):
        self.tasks[task_id] = TaskStatus.QUEUED

    def update_task_status(self, task_id: str, status: TaskStatus):
        if task_id in self.tasks:
            self.tasks[task_id] = status
        else:
            raise ValueError("Task ID not found")

    def get_task_status(self, task_id: str) -> None:
        return self.tasks.get(task_id, None)


# 实例化一个全局的任务管理器
task_manager = TaskManager()


# 装饰器，用于更新任务状态
def update_task_status(func):
    def wrapper(task_id: str, *args, **kwargs):
        try:
            task_manager.update_task_status(task_id, TaskStatus.IN_PROGRESS)
            result = func(task_id, *args, **kwargs)
            task_manager.update_task_status(task_id, TaskStatus.COMPLETED)
            return result
        except Exception as e:
            task_manager.update_task_status(task_id, TaskStatus.QUEUED)
            raise e
    return wrapper
