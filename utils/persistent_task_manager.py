import threading
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import json
import os
from utils.database import db_manager
from utils.task_queue_manager import task_queue_manager
from utils.config_manager import config_manager

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
    client_ip: Optional[str] = None
    source_lang: Optional[str] = None
    target_lang: Optional[str] = None
    via_eng: bool = False
    file_count: int = 0
    total_file_size: int = 0
    
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


class PersistentTaskManager:
    """持久化任务管理器，使用数据库存储任务状态"""
    
    def __init__(self, max_tasks: int = 100, cleanup_interval: int = 300):
        self.max_tasks = max_tasks
        self.cleanup_interval = cleanup_interval
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
            logger.info("持久化任务管理器清理线程已启动")
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
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(hours=24)
            
            # 删除超过24小时的已完成任务
            delete_query = '''
                DELETE FROM tasks 
                WHERE status IN ('completed', 'failed', 'cancelled', 'timeout')
                AND created_at < ?
            '''
            deleted_count = db_manager.execute_update(delete_query, (cutoff_time.isoformat(),))
            
            if deleted_count > 0:
                logger.info(f"清理了 {deleted_count} 个过期任务")
                
        except Exception as e:
            logger.error(f"清理过期任务失败: {e}")
    
    def create_task(self, priority: TaskPriority = TaskPriority.NORMAL, 
                   timeout_seconds: int = 3600, metadata: Optional[Dict[str, Any]] = None,
                   client_ip: Optional[str] = None, source_lang: Optional[str] = None,
                   target_lang: Optional[str] = None, via_eng: bool = False,
                   file_count: int = 0, total_file_size: int = 0) -> str:
        """创建新任务"""
        try:
            # 检查任务数量限制
            current_task_count = self.count_tasks()
            if current_task_count >= self.max_tasks:
                raise RuntimeError(f"任务数量已达上限: {self.max_tasks}")
            
            # 生成任务ID
            import uuid
            task_id = str(uuid.uuid4())
            
            # 创建任务记录
            insert_query = '''
                INSERT INTO tasks (
                    task_id, status, priority, created_at, timeout_seconds,
                    metadata, client_ip, source_lang, target_lang, via_eng,
                    file_count, total_file_size
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            metadata_json = json.dumps(metadata) if metadata else None
            db_manager.execute_update(insert_query, (
                task_id,
                TaskStatus.PENDING.value,
                priority.value,
                datetime.now().isoformat(),
                timeout_seconds,
                metadata_json,
                client_ip,
                source_lang,
                target_lang,
                via_eng,
                file_count,
                total_file_size
            ))
            
            # 添加到任务队列
            if not task_queue_manager.add_task_to_queue(task_id, priority.value):
                # 如果添加到队列失败，删除任务记录
                self._delete_task(task_id)
                raise RuntimeError("任务队列已满，无法创建新任务")
            
            logger.info(f"任务创建成功: {task_id}, 优先级: {priority.value}")
            return task_id
            
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            raise RuntimeError(f"创建任务失败: {e}")
    
    def _delete_task(self, task_id: str) -> bool:
        """删除任务记录"""
        try:
            # 从任务队列中移除
            task_queue_manager.remove_task_from_queue(task_id)
            
            # 删除任务记录
            delete_query = "DELETE FROM tasks WHERE task_id = ?"
            db_manager.execute_update(delete_query, (task_id,))
            
            return True
        except Exception as e:
            logger.error(f"删除任务失败: {task_id}, 错误: {e}")
            return False
    
    def start_task(self, task_id: str) -> bool:
        """开始执行任务"""
        try:
            # 检查任务是否存在且状态为pending
            task = self.get_task_status(task_id)
            if not task:
                raise ValueError(f"任务不存在: {task_id}")
            
            if task['status'] != TaskStatus.PENDING.value:
                raise RuntimeError(f"任务状态不允许开始: {task['status']}")
            
            # 更新任务状态
            update_query = '''
                UPDATE tasks 
                SET status = ?, started_at = ? 
                WHERE task_id = ?
            '''
            db_manager.execute_update(update_query, (
                TaskStatus.PROCESSING.value,
                datetime.now().isoformat(),
                task_id
            ))
            
            logger.info(f"任务开始执行: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"开始任务失败: {task_id}, 错误: {e}")
            return False
    
    def update_task_progress(self, task_id: str, progress: float, 
                           status: Optional[TaskStatus] = None) -> bool:
        """更新任务进度"""
        try:
            # 验证进度值
            if not 0.0 <= progress <= 100.0:
                raise ValueError(f"进度值无效: {progress}, 应在0.0-100.0之间")
            
            # 构建更新查询
            update_fields = ["progress = ?"]
            params = [progress]
            
            if status:
                update_fields.append("status = ?")
                params.append(status.value)
                
                if status == TaskStatus.COMPLETED:
                    update_fields.append("completed_at = ?")
                    params.append(datetime.now().isoformat())
                    progress = 100.0
                elif status == TaskStatus.FAILED:
                    update_fields.append("completed_at = ?")
                    params.append(datetime.now().isoformat())
            
            update_query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE task_id = ?"
            params.append(task_id)
            
            db_manager.execute_update(update_query, tuple(params))
            
            logger.debug(f"任务进度更新: {task_id}, 进度: {progress}%, 状态: {status.value if status else 'unchanged'}")
            return True
            
        except Exception as e:
            logger.error(f"更新任务进度失败: {task_id}, 错误: {e}")
            return False
    
    def complete_task(self, task_id: str, success: bool = True, 
                     error_message: Optional[str] = None) -> bool:
        """完成任务"""
        try:
            # 检查任务状态
            task = self.get_task_status(task_id)
            if not task:
                raise ValueError(f"任务不存在: {task_id}")
            
            if task['status'] != TaskStatus.PROCESSING.value:
                raise RuntimeError(f"任务状态不允许完成: {task['status']}")
            
            # 更新任务状态
            if success:
                status = TaskStatus.COMPLETED
                progress = 100.0
                logger.info(f"任务完成: {task_id}")
            else:
                status = TaskStatus.FAILED
                progress = task.get('progress', 0.0)
                logger.error(f"任务失败: {task_id}, 错误: {error_message}")
            
            update_query = '''
                UPDATE tasks 
                SET status = ?, progress = ?, completed_at = ?, error_message = ?
                WHERE task_id = ?
            '''
            db_manager.execute_update(update_query, (
                status.value,
                progress,
                datetime.now().isoformat(),
                error_message,
                task_id
            ))
            
            # 从队列中移除任务
            task_queue_manager.remove_task_from_queue(task_id)
            
            return True
            
        except Exception as e:
            logger.error(f"完成任务失败: {task_id}, 错误: {e}")
            return False
    
    def cancel_task(self, task_id: str, reason: str = "用户取消") -> bool:
        """取消任务"""
        try:
            # 检查任务状态
            task = self.get_task_status(task_id)
            if not task:
                raise ValueError(f"任务不存在: {task_id}")
            
            if task['status'] not in [TaskStatus.PENDING.value, TaskStatus.PROCESSING.value]:
                raise RuntimeError(f"任务状态不允许取消: {task['status']}")
            
            # 更新任务状态
            update_query = '''
                UPDATE tasks 
                SET status = ?, error_message = ?, completed_at = ?
                WHERE task_id = ?
            '''
            db_manager.execute_update(update_query, (
                TaskStatus.CANCELLED.value,
                reason,
                datetime.now().isoformat(),
                task_id
            ))
            
            # 从队列中移除任务
            task_queue_manager.remove_task_from_queue(task_id)
            
            logger.info(f"任务取消: {task_id}, 原因: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"取消任务失败: {task_id}, 错误: {e}")
            return False
    
    def retry_task(self, task_id: str) -> bool:
        """重试任务"""
        try:
            # 检查任务状态
            task = self.get_task_status(task_id)
            if not task:
                raise ValueError(f"任务不存在: {task_id}")
            
            if task['status'] != TaskStatus.FAILED.value:
                raise RuntimeError(f"任务状态不允许重试: {task['status']}")
            
            if task.get('retry_count', 0) >= task.get('max_retries', 3):
                raise RuntimeError(f"任务重试次数已达上限: {task.get('max_retries', 3)}")
            
            # 更新任务状态
            update_query = '''
                UPDATE tasks 
                SET status = ?, retry_count = ?, error_message = NULL,
                    started_at = NULL, completed_at = NULL, progress = 0.0
                WHERE task_id = ?
            '''
            db_manager.execute_update(update_query, (
                TaskStatus.PENDING.value,
                task.get('retry_count', 0) + 1,
                task_id
            ))
            
            # 重新添加到队列
            if not task_queue_manager.add_task_to_queue(task_id, task.get('priority', 2)):
                logger.warning(f"任务 {task_id} 重试失败：队列已满")
                return False
            
            logger.info(f"任务重试: {task_id}, 重试次数: {task.get('retry_count', 0) + 1}")
            return True
            
        except Exception as e:
            logger.error(f"重试任务失败: {task_id}, 错误: {e}")
            return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        try:
            query = "SELECT * FROM tasks WHERE task_id = ?"
            results = db_manager.execute_query(query, (task_id,))
            
            if results:
                task_data = results[0]
                # 解析metadata JSON
                if task_data.get('metadata'):
                    try:
                        task_data['metadata'] = json.loads(task_data['metadata'])
                    except json.JSONDecodeError:
                        task_data['metadata'] = {}
                
                return task_data
            
            return None
            
        except Exception as e:
            logger.error(f"获取任务状态失败: {task_id}, 错误: {e}")
            return None
    
    def update_task_status(self, task_id: str, status: TaskStatus, progress: Optional[float] = None, 
                          error_message: Optional[str] = None) -> bool:
        """更新任务状态"""
        try:
            # 构建更新查询
            update_fields = ["status = ?"]
            params = [status.value]
            
            if progress is not None:
                update_fields.append("progress = ?")
                params.append(max(0.0, min(100.0, progress)))
            
            if error_message is not None:
                update_fields.append("error_message = ?")
                params.append(error_message)
            
            # 更新时间戳
            if status == TaskStatus.PROCESSING:
                update_fields.append("started_at = ?")
                params.append(datetime.now().isoformat())
            elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.TIMEOUT]:
                update_fields.append("completed_at = ?")
                params.append(datetime.now().isoformat())
            
            update_query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE task_id = ?"
            params.append(task_id)
            
            db_manager.execute_update(update_query, tuple(params))
            
            # 当任务完成、失败、取消或超时时，从队列中删除
            if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.TIMEOUT]:
                try:
                    task_queue_manager.remove_task_from_queue(task_id)
                    logger.info(f"任务 {task_id} 已从队列中删除，状态: {status.value}")
                except Exception as e:
                    logger.warning(f"从队列删除任务失败: {task_id}, 错误: {e}")
            
            logger.info(f"任务状态更新: {task_id}, 状态: {status.value}, 进度: {progress or 'unchanged'}")
            return True
            
        except Exception as e:
            logger.error(f"更新任务状态失败: {task_id}, 错误: {e}")
            return False
    
    def get_all_tasks(self, status_filter: Optional[TaskStatus] = None, 
                      limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取所有任务"""
        try:
            if status_filter:
                query = "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC"
                params = (status_filter.value,)
            else:
                query = "SELECT * FROM tasks ORDER BY created_at DESC"
                params = ()
            
            if limit:
                query += f" LIMIT {limit}"
            
            results = db_manager.execute_query(query, params)
            
            # 解析metadata JSON
            for task in results:
                if task.get('metadata'):
                    try:
                        task['metadata'] = json.loads(task['metadata'])
                    except json.JSONDecodeError:
                        task['metadata'] = {}
            
            return results
            
        except Exception as e:
            logger.error(f"获取所有任务失败: {e}")
            return []
    
    def count_tasks(self, status_filter: Optional[TaskStatus] = None) -> int:
        """统计任务数量"""
        try:
            if status_filter:
                query = "SELECT COUNT(*) as count FROM tasks WHERE status = ?"
                params = (status_filter.value,)
            else:
                query = "SELECT COUNT(*) as count FROM tasks WHERE status IN ('pending', 'processing')"
                params = ()
            
            results = db_manager.execute_query(query, params)
            return results[0]['count'] if results else 0
            
        except Exception as e:
            logger.error(f"统计任务数量失败: {e}")
            return 0
    
    def get_task_metrics(self) -> Dict[str, Any]:
        """获取任务统计指标"""
        try:
            # 获取各种状态的任务数量
            status_counts_query = '''
                SELECT 
                    status,
                    COUNT(*) as count
                FROM tasks 
                GROUP BY status
            '''
            status_counts = db_manager.execute_query(status_counts_query)
            
            # 转换为字典格式
            status_dict = {row['status']: row['count'] for row in status_counts}
            
            total_tasks = sum(status_dict.values())
            completed_tasks = status_dict.get(TaskStatus.COMPLETED.value, 0)
            failed_tasks = status_dict.get(TaskStatus.FAILED.value, 0)
            
            # 计算成功率
            total_finished = completed_tasks + failed_tasks
            success_rate = (completed_tasks / total_finished * 100) if total_finished > 0 else 0
            
            # 获取队列状态
            queue_status = task_queue_manager.get_queue_status()
            
            return {
                'total_tasks': total_tasks,
                'pending_tasks': status_dict.get(TaskStatus.PENDING.value, 0),
                'processing_tasks': status_dict.get(TaskStatus.PROCESSING.value, 0),
                'completed_tasks': completed_tasks,
                'failed_tasks': failed_tasks,
                'cancelled_tasks': status_dict.get(TaskStatus.CANCELLED.value, 0),
                'timeout_tasks': status_dict.get(TaskStatus.TIMEOUT.value, 0),
                'success_rate': round(success_rate, 2),
                'max_tasks': self.max_tasks,
                'queue_status': queue_status
            }
            
        except Exception as e:
            logger.error(f"获取任务统计指标失败: {e}")
            return {}
    
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
    
    def shutdown(self) -> None:
        """关闭任务管理器"""
        try:
            self.running = False
            if self.cleanup_thread and self.cleanup_thread.is_alive():
                self.cleanup_thread.join(timeout=5)
            
            logger.info("持久化任务管理器已关闭")
            
        except Exception as e:
            logger.error(f"关闭任务管理器失败: {e}")


# 创建全局持久化任务管理器实例
persistent_task_manager = PersistentTaskManager()
