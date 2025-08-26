import threading
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum
from utils.database import db_manager
from utils.config_manager import config_manager

logger = logging.getLogger(__name__)


class QueueStatus(Enum):
    """队列状态枚举"""
    IDLE = "idle"
    PROCESSING = "processing"
    FULL = "full"
    ERROR = "error"


class TaskQueueManager:
    """任务队列管理器，负责任务的排队、分配和调度"""
    
    def __init__(self):
        self.max_queue_size = config_manager.getint('SETTINGS', 'MAX_TASK_QUEUE_SIZE', 50)
        self.max_concurrent_tasks = config_manager.getint('SETTINGS', 'MAX_CONCURRENT_TASKS', 10)
        self.gpu_monitor_interval = config_manager.getint('GPU', 'GPU_MONITOR_INTERVAL', 10)
        self.lock = threading.RLock()
        self.running = False
        self.scheduler_thread = None
        self.gpu_monitor_thread = None
        
        # 启动调度器和监控线程
        self._start_scheduler()
        self._start_gpu_monitor()
    
    def _start_scheduler(self):
        """启动任务调度器线程"""
        try:
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            self.running = True
            logger.info("任务调度器线程已启动")
        except Exception as e:
            logger.error(f"启动任务调度器失败: {e}")
    
    def _start_gpu_monitor(self):
        """启动GPU监控线程"""
        try:
            self.gpu_monitor_thread = threading.Thread(target=self._gpu_monitor_loop, daemon=True)
            self.gpu_monitor_thread.start()
            logger.info("GPU监控线程已启动")
        except Exception as e:
            logger.error(f"启动GPU监控失败: {e}")
    
    def _scheduler_loop(self):
        """任务调度主循环"""
        while self.running:
            try:
                # 检查是否有待处理的任务
                pending_tasks = self._get_pending_tasks()
                if pending_tasks:
                    # 尝试分配任务到可用的GPU
                    self._assign_tasks_to_gpus(pending_tasks)
                
                # 检查已完成的任务，释放GPU资源
                self._check_completed_tasks()
                
                # 等待一段时间再继续
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"任务调度循环异常: {e}")
                time.sleep(10)  # 出错后等待更长时间
    
    def _gpu_monitor_loop(self):
        """GPU监控循环"""
        while self.running:
            try:
                # 更新GPU状态
                self._update_gpu_status()
                
                # 等待下次监控
                time.sleep(self.gpu_monitor_interval)
                
            except Exception as e:
                logger.error(f"GPU监控循环异常: {e}")
                time.sleep(30)  # 出错后等待30秒
    
    def _get_pending_tasks(self) -> List[Dict[str, Any]]:
        """获取待处理的任务"""
        try:
            query = '''
                SELECT t.*, q.priority as queue_priority
                FROM tasks t
                JOIN task_queue q ON t.task_id = q.task_id
                WHERE t.status = 'pending'
                AND q.assigned_gpu IS NULL
                ORDER BY q.priority DESC, q.created_at ASC
                LIMIT ?
            '''
            return db_manager.execute_query(query, (self.max_concurrent_tasks,))
        except Exception as e:
            logger.error(f"获取待处理任务失败: {e}")
            return []
    
    def _assign_tasks_to_gpus(self, pending_tasks: List[Dict[str, Any]]):
        """将任务分配给可用的GPU"""
        try:
            # 获取可用的GPU
            available_gpus = self._get_available_gpus()
            if not available_gpus:
                logger.debug("没有可用的GPU，任务等待中...")
                return
            
            # 按优先级分配任务
            for task in pending_tasks:
                if not available_gpus:
                    break
                
                # 选择最适合的GPU
                best_gpu = self._select_best_gpu(available_gpus, task)
                if best_gpu:
                    # 分配任务到GPU
                    if self._assign_task_to_gpu(task['task_id'], best_gpu['gpu_id']):
                        # 从可用GPU列表中移除
                        available_gpus = [g for g in available_gpus if g['gpu_id'] != best_gpu['gpu_id']]
                        logger.info(f"任务 {task['task_id']} 已分配到GPU {best_gpu['gpu_id']}")
                    else:
                        logger.warning(f"任务 {task['task_id']} 分配GPU失败")
                
        except Exception as e:
            logger.error(f"分配任务到GPU失败: {e}")
    
    def _get_available_gpus(self) -> List[Dict[str, Any]]:
        """获取可用的GPU"""
        try:
            query = '''
                SELECT * FROM gpu_status 
                WHERE is_available = TRUE 
                AND current_task_id IS NULL
                ORDER BY memory_free DESC
            '''
            return db_manager.execute_query(query)
        except Exception as e:
            logger.error(f"获取可用GPU失败: {e}")
            return []
    
    def _select_best_gpu(self, available_gpus: List[Dict[str, Any]], task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """选择最适合的GPU"""
        if not available_gpus:
            return None
        
        # 简单的选择策略：选择内存最充足的GPU
        # 可以根据任务类型、GPU负载等进行更复杂的策略
        return max(available_gpus, key=lambda g: g.get('memory_free', 0))
    
    def _assign_task_to_gpu(self, task_id: str, gpu_id: str) -> bool:
        """将任务分配给指定的GPU"""
        try:
            # 更新任务队列中的GPU分配
            update_queue = '''
                UPDATE task_queue 
                SET assigned_gpu = ?, assigned_at = ? 
                WHERE task_id = ?
            '''
            db_manager.execute_update(update_queue, (gpu_id, datetime.now().isoformat(), task_id))
            
            # 更新GPU状态
            update_gpu = '''
                UPDATE gpu_status 
                SET current_task_id = ?, is_available = FALSE 
                WHERE gpu_id = ?
            '''
            db_manager.execute_update(update_gpu, (task_id, gpu_id))
            
            # 更新任务状态为处理中
            update_task = '''
                UPDATE tasks 
                SET status = 'processing', started_at = ? 
                WHERE task_id = ?
            '''
            db_manager.execute_update(update_task, (datetime.now().isoformat(), task_id))
            
            return True
            
        except Exception as e:
            logger.error(f"分配任务到GPU失败: {task_id} -> {gpu_id}, 错误: {e}")
            return False
    
    def _check_completed_tasks(self):
        """检查已完成的任务，释放GPU资源并从队列中删除"""
        try:
            # 查找已完成的任务
            query = '''
                SELECT t.task_id, q.assigned_gpu, t.status
                FROM tasks t
                JOIN task_queue q ON t.task_id = q.task_id
                WHERE t.status IN ('completed', 'failed', 'cancelled', 'timeout')
                AND q.assigned_gpu IS NOT NULL
            '''
            completed_tasks = db_manager.execute_query(query)
            
            for task in completed_tasks:
                task_id = task['task_id']
                gpu_id = task['assigned_gpu']
                status = task['status']
                
                # 释放GPU资源
                self._release_gpu_resource(gpu_id)
                
                # 从队列中删除已完成的任务
                try:
                    self.remove_task_from_queue(task_id)
                    logger.info(f"已完成任务 {task_id} (状态: {status}) 已从队列中删除")
                except Exception as e:
                    logger.error(f"从队列删除已完成任务失败: {task_id}, 错误: {e}")
                
        except Exception as e:
            logger.error(f"检查已完成任务失败: {e}")
    
    def _release_gpu_resource(self, gpu_id: str):
        """释放GPU资源"""
        try:
            update_gpu = '''
                UPDATE gpu_status 
                SET current_task_id = NULL, is_available = TRUE 
                WHERE gpu_id = ?
            '''
            db_manager.execute_update(update_gpu, (gpu_id,))
            logger.debug(f"GPU {gpu_id} 资源已释放")
            
        except Exception as e:
            logger.error(f"释放GPU资源失败: {gpu_id}, 错误: {e}")
    
    def _update_gpu_status(self):
        """更新GPU状态"""
        try:
            # 这里应该调用实际的GPU监控代码
            # 暂时使用模拟数据
            from models.translateModel import TranslatorSingleton
            
            if hasattr(TranslatorSingleton, 'get_gpu_status'):
                gpu_status = TranslatorSingleton.get_gpu_status()
                if gpu_status and 'gpus' in gpu_status:
                    for gpu_info in gpu_status['gpus']:
                        self._update_single_gpu_status(gpu_info)
                        
        except Exception as e:
            logger.error(f"更新GPU状态失败: {e}")
    
    def _update_single_gpu_status(self, gpu_info: Dict[str, Any]):
        """更新单个GPU的状态"""
        try:
            # 检查GPU是否已存在
            check_query = "SELECT gpu_id FROM gpu_status WHERE gpu_id = ?"
            existing = db_manager.execute_query(check_query, (gpu_info.get('device_id'),))
            
            if existing:
                # 更新现有记录
                update_query = '''
                    UPDATE gpu_status SET
                        memory_total = ?,
                        memory_used = ?,
                        memory_free = ?,
                        utilization = ?,
                        temperature = ?,
                        last_updated = ?
                    WHERE gpu_id = ?
                '''
                db_manager.execute_update(update_query, (
                    gpu_info.get('memory_total', 0),
                    gpu_info.get('memory_used', 0),
                    gpu_info.get('memory_free', 0),
                    gpu_info.get('utilization', 0),
                    gpu_info.get('temperature', 0),
                    datetime.now().isoformat(),
                    gpu_info.get('device_id')
                ))
            else:
                # 插入新记录
                insert_query = '''
                    INSERT INTO gpu_status (
                        gpu_id, device_name, memory_total, memory_used, 
                        memory_free, utilization, temperature, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                '''
                db_manager.execute_update(insert_query, (
                    gpu_info.get('device_id'),
                    gpu_info.get('name', 'Unknown'),
                    gpu_info.get('memory_total', 0),
                    gpu_info.get('memory_used', 0),
                    gpu_info.get('memory_free', 0),
                    gpu_info.get('utilization', 0),
                    gpu_info.get('temperature', 0),
                    datetime.now().isoformat()
                ))
                
        except Exception as e:
            logger.error(f"更新GPU状态失败: {gpu_info.get('device_id', 'unknown')}, 错误: {e}")
    
    def add_task_to_queue(self, task_id: str, priority: int = 2) -> bool:
        """将任务添加到队列"""
        try:
            # 检查队列是否已满
            current_queue_size = self._get_queue_size()
            if current_queue_size >= self.max_queue_size:
                logger.warning(f"任务队列已满，无法添加任务: {task_id}")
                return False
            
            # 添加到队列
            insert_query = '''
                INSERT INTO task_queue (task_id, priority, created_at)
                VALUES (?, ?, ?)
            '''
            db_manager.execute_update(insert_query, (task_id, priority, datetime.now().isoformat()))
            
            logger.info(f"任务 {task_id} 已添加到队列，优先级: {priority}")
            return True
            
        except Exception as e:
            logger.error(f"添加任务到队列失败: {task_id}, 错误: {e}")
            return False
    
    def remove_task_from_queue(self, task_id: str) -> bool:
        """从队列中移除任务"""
        try:
            delete_query = "DELETE FROM task_queue WHERE task_id = ?"
            db_manager.execute_update(delete_query, (task_id,))
            logger.info(f"任务 {task_id} 已从队列中移除")
            return True
            
        except Exception as e:
            logger.error(f"从队列移除任务失败: {task_id}, 错误: {e}")
            return False
    
    def _get_queue_size(self) -> int:
        """获取当前队列大小"""
        try:
            query = "SELECT COUNT(*) as count FROM task_queue"
            result = db_manager.execute_query(query)
            return result[0]['count'] if result else 0
        except Exception as e:
            logger.error(f"获取队列大小失败: {e}")
            return 0
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态信息"""
        try:
            # 获取队列统计信息
            queue_stats_query = '''
                SELECT 
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN assigned_gpu IS NULL THEN 1 ELSE 0 END) as waiting_tasks,
                    SUM(CASE WHEN assigned_gpu IS NOT NULL THEN 1 ELSE 0 END) as processing_tasks
                FROM task_queue
            '''
            queue_stats = db_manager.execute_query(queue_stats_query)
            
            # 获取GPU统计信息
            gpu_stats_query = '''
                SELECT 
                    COUNT(*) as total_gpus,
                    SUM(CASE WHEN is_available THEN 1 ELSE 0 END) as available_gpus,
                    SUM(CASE WHEN NOT is_available THEN 1 ELSE 0 END) as busy_gpus
                FROM gpu_status
            '''
            gpu_stats = db_manager.execute_query(gpu_stats_query)
            
            return {
                'queue_status': QueueStatus.PROCESSING.value if queue_stats[0]['waiting_tasks'] > 0 else QueueStatus.IDLE.value,
                'queue_stats': queue_stats[0] if queue_stats else {},
                'gpu_stats': gpu_stats[0] if gpu_stats else {},
                'max_queue_size': self.max_queue_size,
                'max_concurrent_tasks': self.max_concurrent_tasks,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取队列状态失败: {e}")
            return {
                'queue_status': QueueStatus.ERROR.value,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def shutdown(self):
        """关闭任务队列管理器"""
        try:
            self.running = False
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)
            if self.gpu_monitor_thread and self.gpu_monitor_thread.is_alive():
                self.gpu_monitor_thread.join(timeout=5)
            logger.info("任务队列管理器已关闭")
            
        except Exception as e:
            logger.error(f"关闭任务队列管理器失败: {e}")


# 创建全局任务队列管理器实例
task_queue_manager = TaskQueueManager()
