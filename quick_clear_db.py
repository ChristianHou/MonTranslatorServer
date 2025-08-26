#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速数据库清空脚本
简单快速地清空所有数据库表
"""

import sqlite3
import os

def quick_clear():
    """快速清空数据库"""
    db_path = "tasks.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🗑️  正在清空数据库...")
        
        # 清空所有表
        cursor.execute("DELETE FROM task_queue")
        cursor.execute("DELETE FROM gpu_status")
        cursor.execute("DELETE FROM tasks")
        
        # 重置自增ID
        cursor.execute("DELETE FROM sqlite_sequence")
        
        conn.commit()
        conn.close()
        
        print("✅ 数据库清空完成！")
        
    except Exception as e:
        print(f"❌ 清空失败: {e}")

if __name__ == "__main__":
    quick_clear()
