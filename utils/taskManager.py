# task_manager.py
import os
from enum import Enum


# 定义任务状态枚举类
class TaskStatus(str, Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    DOWNLOADED = "downloaded"


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

    def delete_task_status(self, task_id: str) -> None:
        del self.tasks[task_id]

    def delete_downloaded_task_folders(self, download_directory: str):
        """删除状态为'已下载'的任务文件夹"""
        to_delete = [task_id for task_id, status in self.tasks.items() if status == TaskStatus.DOWNLOADED or status == TaskStatus.FAILED]
        for task_id in to_delete:
            folder_path = os.path.join(download_directory, task_id)
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                self.delete_folder_contents(folder_path)
                os.rmdir(folder_path)
                self.delete_task_status(task_id)

    def delete_folder_contents(self, folder_path: str):
        """删除文件夹中的所有内容，包括子文件夹"""
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                self.delete_folder_contents(file_path)
                os.rmdir(file_path)


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
            task_manager.update_task_status(task_id, TaskStatus.FAILED)
            raise e

    return wrapper
