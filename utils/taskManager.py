# task_manager.py
import threading
import time
import uuid
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class TaskInfo:
    """任务信息数据类"""
    task_id: str
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 3600  # 1小时超时
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['status'] = self.status.value
        data['priority'] = self.priority.value
        data['created_at'] = self.created_at.isoformat()
        if self.started_at:
            data['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data


class TaskManager:
    """改进的任务管理器，具有完善的异常处理和状态管理"""
    
    def __init__(self, max_tasks: int = 100, cleanup_interval: int = 300):
        self.max_tasks = max_tasks
        self.cleanup_interval = cleanup_interval
        self.tasks: Dict[str, TaskInfo] = {}
        self.lock = threading.RLock()
        self.cleanup_thread = None
        self.running = False
        
        # 启动清理线程
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self) -> None:
        """启动清理线程"""
        try:
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self.cleanup_thread.start()
            self.running = True
            logger.info("任务管理器清理线程已启动")
        except Exception as e:
            logger.error(f"启动清理线程失败: {e}")
    
    def _cleanup_loop(self) -> None:
        """清理循环"""
        while self.running:
            try:
                time.sleep(self.cleanup_interval)
                self._cleanup_expired_tasks()
            except Exception as e:
                logger.error(f"清理循环异常: {e}")
                time.sleep(60)  # 出错后等待1分钟再继续
    
    def _cleanup_expired_tasks(self) -> None:
        """清理过期的任务"""
        try:
            with self.lock:
                current_time = datetime.now()
                expired_tasks = []
                
                for task_id, task in self.tasks.items():
                    # 检查超时任务
                    if (task.status in [TaskStatus.PENDING, TaskStatus.PROCESSING] and
                        task.created_at + timedelta(seconds=task.timeout_seconds) < current_time):
                        task.status = TaskStatus.TIMEOUT
                        task.error_message = "任务超时"
                        expired_tasks.append(task_id)
                        logger.warning(f"任务超时: {task_id}")
                    
                    # 清理已完成且超过24小时的任务
                    elif (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.TIMEOUT] and
                          task.created_at + timedelta(hours=24) < current_time):
                        expired_tasks.append(task_id)
                
                # 删除过期任务
                for task_id in expired_tasks:
                    del self.tasks[task_id]
                
                if expired_tasks:
                    logger.info(f"清理了 {len(expired_tasks)} 个过期任务")
                    
        except Exception as e:
            logger.error(f"清理过期任务失败: {e}")
    
    def create_task(self, priority: TaskPriority = TaskPriority.NORMAL, 
                   timeout_seconds: int = 3600, metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建新任务"""
        try:
            with self.lock:
                # 检查任务数量限制
                if len(self.tasks) >= self.max_tasks:
                    raise RuntimeError(f"任务数量已达上限: {self.max_tasks}")
                
                # 生成任务ID
                task_id = str(uuid.uuid4())
                
                # 创建任务信息
                task = TaskInfo(
                    task_id=task_id,
                    status=TaskStatus.PENDING,
                    priority=priority,
                    created_at=datetime.now(),
                    timeout_seconds=timeout_seconds,
                    metadata=metadata or {}
                )
                
                self.tasks[task_id] = task
                logger.info(f"任务创建成功: {task_id}, 优先级: {priority.value}")
                
                return task_id
                
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            raise RuntimeError(f"创建任务失败: {e}")
    
    def start_task(self, task_id: str) -> bool:
        """开始执行任务"""
        try:
            with self.lock:
                if task_id not in self.tasks:
                    raise ValueError(f"任务不存在: {task_id}")
                
                task = self.tasks[task_id]
                
                if task.status != TaskStatus.PENDING:
                    raise RuntimeError(f"任务状态不允许开始: {task.status.value}")
                
                task.status = TaskStatus.PROCESSING
                task.started_at = datetime.now()
                
                logger.info(f"任务开始执行: {task_id}")
                return True
                
        except Exception as e:
            logger.error(f"开始任务失败: {task_id}, 错误: {e}")
            return False
    
    def update_task_progress(self, task_id: str, progress: float, 
                           status: Optional[TaskStatus] = None) -> bool:
        """更新任务进度"""
        try:
            with self.lock:
                if task_id not in self.tasks:
                    raise ValueError(f"任务不存在: {task_id}")
                
                task = self.tasks[task_id]
                
                # 验证进度值
                if not 0.0 <= progress <= 100.0:
                    raise ValueError(f"进度值无效: {progress}, 应在0.0-100.0之间")
                
                task.progress = progress
                
                if status:
                    task.status = status
                    if status == TaskStatus.COMPLETED:
                        task.completed_at = datetime.now()
                        task.progress = 100.0
                    elif status == TaskStatus.FAILED:
                        task.completed_at = datetime.now()
                
                logger.debug(f"任务进度更新: {task_id}, 进度: {progress}%, 状态: {task.status.value}")
                return True
                
        except Exception as e:
            logger.error(f"更新任务进度失败: {task_id}, 错误: {e}")
            return False
    
    def complete_task(self, task_id: str, success: bool = True, 
                     error_message: Optional[str] = None) -> bool:
        """完成任务"""
        try:
            with self.lock:
                if task_id not in self.tasks:
                    raise ValueError(f"任务不存在: {task_id}")
                
                task = self.tasks[task_id]
                
                if task.status != TaskStatus.PROCESSING:
                    raise RuntimeError(f"任务状态不允许完成: {task.status.value}")
                
                if success:
                    task.status = TaskStatus.COMPLETED
                    task.progress = 100.0
                    logger.info(f"任务完成: {task_id}")
                else:
                    task.status = TaskStatus.FAILED
                    task.error_message = error_message or "任务执行失败"
                    logger.error(f"任务失败: {task_id}, 错误: {error_message}")
                
                task.completed_at = datetime.now()
                return True
                
        except Exception as e:
            logger.error(f"完成任务失败: {task_id}, 错误: {e}")
            return False
    
    def cancel_task(self, task_id: str, reason: str = "用户取消") -> bool:
        """取消任务"""
        try:
            with self.lock:
                if task_id not in self.tasks:
                    raise ValueError(f"任务不存在: {task_id}")
                
                task = self.tasks[task_id]
                
                if task.status not in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
                    raise RuntimeError(f"任务状态不允许取消: {task.status.value}")
                
                task.status = TaskStatus.CANCELLED
                task.error_message = reason
                task.completed_at = datetime.now()
                
                logger.info(f"任务取消: {task_id}, 原因: {reason}")
                return True
                
        except Exception as e:
            logger.error(f"取消任务失败: {task_id}, 错误: {e}")
            return False
    
    def retry_task(self, task_id: str) -> bool:
        """重试任务"""
        try:
            with self.lock:
                if task_id not in self.tasks:
                    raise ValueError(f"任务不存在: {task_id}")
                
                task = self.tasks[task_id]
                
                if task.status != TaskStatus.FAILED:
                    raise RuntimeError(f"任务状态不允许重试: {task.status.value}")
                
                if task.retry_count >= task.max_retries:
                    raise RuntimeError(f"任务重试次数已达上限: {task.max_retries}")
                
                task.status = TaskStatus.PENDING
                task.retry_count += 1
                task.error_message = None
                task.started_at = None
                task.completed_at = None
                task.progress = 0.0
                
                logger.info(f"任务重试: {task_id}, 重试次数: {task.retry_count}")
                return True
                
        except Exception as e:
            logger.error(f"重试任务失败: {task_id}, 错误: {e}")
            return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        try:
            with self.lock:
                if task_id not in self.tasks:
                    return None
                
                task = self.tasks[task_id]
                return task.to_dict()
                
        except Exception as e:
            logger.error(f"获取任务状态失败: {task_id}, 错误: {e}")
            return None
    
    def update_task_status(self, task_id: str, status: TaskStatus, progress: Optional[float] = None, 
                          error_message: Optional[str] = None) -> bool:
        """更新任务状态"""
        try:
            with self.lock:
                if task_id not in self.tasks:
                    logger.warning(f"任务不存在，无法更新状态: {task_id}")
                    return False
                
                task = self.tasks[task_id]
                old_status = task.status
                task.status = status
                
                # 更新进度
                if progress is not None:
                    task.progress = max(0.0, min(100.0, progress))
                
                # 更新错误信息
                if error_message is not None:
                    task.error_message = error_message
                
                # 更新时间戳
                if status == TaskStatus.PROCESSING and not task.started_at:
                    task.started_at = datetime.now()
                elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.TIMEOUT]:
                    task.completed_at = datetime.now()
                
                logger.info(f"任务状态更新: {task_id}, {old_status.value} -> {status.value}, 进度: {task.progress:.1f}%")
                return True
                
        except Exception as e:
            logger.error(f"更新任务状态失败: {task_id}, 错误: {e}")
            return False
    
    def delete_downloaded_task_folders(self, download_directory: str) -> None:
        """删除已下载的任务文件夹（定时清理）"""
        try:
            import os
            import shutil
            from datetime import datetime, timedelta
            
            # 获取当前时间
            now = datetime.now()
            # 删除超过7天的文件夹
            cutoff_time = now - timedelta(days=7)
            
            if not os.path.exists(download_directory):
                logger.info(f"下载目录不存在: {download_directory}")
                return
            
            deleted_count = 0
            for item in os.listdir(download_directory):
                item_path = os.path.join(download_directory, item)
                
                # 检查是否是目录
                if os.path.isdir(item_path):
                    try:
                        # 获取目录的修改时间
                        mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
                        
                        # 如果目录超过7天，则删除
                        if mtime < cutoff_time:
                            shutil.rmtree(item_path)
                            deleted_count += 1
                            logger.info(f"删除过期下载目录: {item_path}")
                    except Exception as e:
                        logger.warning(f"删除目录失败: {item_path}, 错误: {e}")
                        continue
            
            if deleted_count > 0:
                logger.info(f"定时清理完成，删除了 {deleted_count} 个过期下载目录")
            else:
                logger.info("定时清理完成，没有需要删除的过期目录")
                
        except Exception as e:
            logger.error(f"定时清理下载目录失败: {e}")
    
    def get_all_tasks(self, status_filter: Optional[TaskStatus] = None) -> List[Dict[str, Any]]:
        """获取所有任务"""
        try:
            with self.lock:
                if status_filter:
                    tasks = [task.to_dict() for task in self.tasks.values() 
                            if task.status == status_filter]
                else:
                    tasks = [task.to_dict() for task in self.tasks.values()]
                
                # 按创建时间排序
                tasks.sort(key=lambda x: x['created_at'])
                return tasks
                
        except Exception as e:
            logger.error(f"获取所有任务失败: {e}")
            return []
    
    def count_tasks(self, status_filter: Optional[TaskStatus] = None) -> int:
        """统计任务数量"""
        try:
            with self.lock:
                if status_filter:
                    return sum(1 for task in self.tasks.values() 
                             if task.status == status_filter)
                else:
                    return len(self.tasks)
                    
        except Exception as e:
            logger.error(f"统计任务数量失败: {e}")
            return 0
    
    def get_task_metrics(self) -> Dict[str, Any]:
        """获取任务统计指标"""
        try:
            with self.lock:
                total_tasks = len(self.tasks)
                pending_tasks = sum(1 for task in self.tasks.values() 
                                  if task.status == TaskStatus.PENDING)
                processing_tasks = sum(1 for task in self.tasks.values() 
                                    if task.status == TaskStatus.PROCESSING)
                completed_tasks = sum(1 for task in self.tasks.values() 
                                   if task.status == TaskStatus.COMPLETED)
                failed_tasks = sum(1 for task in self.tasks.values() 
                                 if task.status == TaskStatus.FAILED)
                
                # 计算成功率
                total_finished = completed_tasks + failed_tasks
                success_rate = (completed_tasks / total_finished * 100) if total_finished > 0 else 0
                
                return {
                    'total_tasks': total_tasks,
                    'pending_tasks': pending_tasks,
                    'processing_tasks': processing_tasks,
                    'completed_tasks': completed_tasks,
                    'failed_tasks': failed_tasks,
                    'success_rate': round(success_rate, 2),
                    'max_tasks': self.max_tasks
                }
                
        except Exception as e:
            logger.error(f"获取任务统计指标失败: {e}")
            return {}
    
    def save_tasks_to_file(self, filepath: str) -> bool:
        """保存任务状态到文件"""
        try:
            with self.lock:
                tasks_data = [task.to_dict() for task in self.tasks.values()]
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(tasks_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"任务状态已保存到文件: {filepath}")
                return True
                
        except Exception as e:
            logger.error(f"保存任务状态到文件失败: {e}")
            return False
    
    def load_tasks_from_file(self, filepath: str) -> bool:
        """从文件加载任务状态"""
        try:
            if not os.path.exists(filepath):
                logger.warning(f"任务状态文件不存在: {filepath}")
                return False
            
            with open(filepath, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)
            
            with self.lock:
                # 清空现有任务
                self.tasks.clear()
                
                # 加载任务数据
                for task_dict in tasks_data:
                    try:
                        # 转换状态枚举
                        task_dict['status'] = TaskStatus(task_dict['status'])
                        task_dict['priority'] = TaskPriority(task_dict['priority'])
                        
                        # 转换时间字符串
                        task_dict['created_at'] = datetime.fromisoformat(task_dict['created_at'])
                        if task_dict.get('started_at'):
                            task_dict['started_at'] = datetime.fromisoformat(task_dict['started_at'])
                        if task_dict.get('completed_at'):
                            task_dict['completed_at'] = datetime.fromisoformat(task_dict['completed_at'])
                        
                        # 创建任务对象
                        task = TaskInfo(**task_dict)
                        self.tasks[task.task_id] = task
                        
                    except Exception as e:
                        logger.warning(f"加载任务数据失败: {task_dict}, 错误: {e}")
                        continue
                
                logger.info(f"从文件加载了 {len(self.tasks)} 个任务: {filepath}")
                return True
                
        except Exception as e:
            logger.error(f"从文件加载任务状态失败: {e}")
            return False
    
    def shutdown(self) -> None:
        """关闭任务管理器"""
        try:
            self.running = False
            if self.cleanup_thread and self.cleanup_thread.is_alive():
                self.cleanup_thread.join(timeout=5)
            
            # 保存当前任务状态
            self.save_tasks_to_file("tasks_backup.json")
            logger.info("任务管理器已关闭")
            
        except Exception as e:
            logger.error(f"关闭任务管理器失败: {e}")


# 创建全局任务管理器实例
task_manager = TaskManager()


def update_task_status(func):
    """任务状态更新装饰器"""
    def wrapper(*args, **kwargs):
        # 从函数参数中提取task_id
        task_id = None
        
        # 方法1：从位置参数中查找（第一个参数）
        if args and len(args) > 0:
            task_id = args[0]
        
        # 方法2：从关键字参数中查找
        if not task_id and 'task_id' in kwargs:
            task_id = kwargs['task_id']
        
        # 方法3：从函数签名中查找第一个参数名
        if not task_id:
            import inspect
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
            if param_names and 'task_id' in param_names:
                # 如果task_id在参数列表中，尝试从args或kwargs中获取
                if 'task_id' in kwargs:
                    task_id = kwargs['task_id']
                elif len(args) > 0:
                    task_id = args[0]
        
        if not task_id:
            logger.warning("装饰器无法找到task_id参数")
            return func(*args, **kwargs)
        
        try:
            # 更新任务状态为处理中
            task_manager.update_task_status(task_id, TaskStatus.PROCESSING, progress=25)
            
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 更新任务状态为已完成
            task_manager.update_task_status(task_id, TaskStatus.COMPLETED, progress=100)
            
            return result
            
        except Exception as e:
            # 更新任务状态为失败
            error_message = str(e)
            task_manager.update_task_status(task_id, TaskStatus.FAILED, error_message=error_message)
            logger.error(f"任务执行失败: {task_id}, 错误: {error_message}")
            raise e
    
    return wrapper
