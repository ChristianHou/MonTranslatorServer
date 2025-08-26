import sqlite3
import threading
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器，负责SQLite数据库的连接和操作"""
    
    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path
        self.lock = threading.RLock()
        self._init_database()
    
    def _init_database(self):
        """初始化数据库和表结构"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 创建任务表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        task_id TEXT PRIMARY KEY,
                        status TEXT NOT NULL,
                        priority INTEGER NOT NULL,
                        created_at TEXT NOT NULL,
                        started_at TEXT,
                        completed_at TEXT,
                        progress REAL DEFAULT 0.0,
                        error_message TEXT,
                        retry_count INTEGER DEFAULT 0,
                        max_retries INTEGER DEFAULT 3,
                        timeout_seconds INTEGER DEFAULT 3600,
                        metadata TEXT,
                        client_ip TEXT,
                        source_lang TEXT,
                        target_lang TEXT,
                        via_eng BOOLEAN DEFAULT FALSE,
                        file_count INTEGER DEFAULT 0,
                        total_file_size INTEGER DEFAULT 0
                    )
                ''')
                
                # 创建任务队列表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS task_queue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id TEXT NOT NULL,
                        priority INTEGER NOT NULL,
                        created_at TEXT NOT NULL,
                        assigned_gpu TEXT,
                        assigned_at TEXT,
                        FOREIGN KEY (task_id) REFERENCES tasks (task_id)
                    )
                ''')
                
                # 创建GPU状态表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS gpu_status (
                        gpu_id TEXT PRIMARY KEY,
                        device_name TEXT,
                        memory_total INTEGER,
                        memory_used INTEGER,
                        memory_free INTEGER,
                        utilization REAL,
                        temperature REAL,
                        last_updated TEXT,
                        is_available BOOLEAN DEFAULT TRUE,
                        current_task_id TEXT,
                        FOREIGN KEY (current_task_id) REFERENCES tasks (task_id)
                    )
                ''')
                
                # 创建索引以提高查询性能
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_queue_priority ON task_queue(priority DESC, created_at ASC)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_gpu_available ON gpu_status(is_available)')
                
                conn.commit()
                conn.close()
                logger.info("数据库初始化完成")
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def get_connection(self):
        """获取数据库连接"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
            return conn
        except Exception as e:
            logger.error(f"获取数据库连接失败: {e}")
            raise
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行查询并返回结果"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                # 转换为字典列表
                if results:
                    return [dict(row) for row in results]
                return []
                
        except Exception as e:
            logger.error(f"执行查询失败: {e}, 查询: {query}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """执行更新操作并返回影响的行数"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount
                
        except Exception as e:
            logger.error(f"执行更新失败: {e}, 查询: {query}")
            if 'conn' in locals():
                conn.rollback()
            raise
        finally:
            if 'conn' in locals():
                conn.close()
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """批量执行操作"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount
                
        except Exception as e:
            logger.error(f"批量执行失败: {e}, 查询: {query}")
            if 'conn' in locals():
                conn.rollback()
            raise
        finally:
            if 'conn' in locals():
                conn.close()


# 创建全局数据库管理器实例
db_manager = DatabaseManager()
