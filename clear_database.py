#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库清空脚本
用于清空所有任务管理相关的数据库表
"""

import sqlite3
import os
import sys
from pathlib import Path
import time

def clear_database(db_path: str = "tasks.db"):
    """清空数据库中的所有表"""
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"🔗 已连接到数据库: {db_path}")
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 发现以下表: {', '.join(tables)}")
        
        # 关闭外键约束检查
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # 清空每个表
        for table in tables:
            if table != 'sqlite_sequence':  # 跳过系统表
                cursor.execute(f"DELETE FROM {table}")
                affected_rows = cursor.rowcount
                print(f"🗑️  清空表 {table}: 删除了 {affected_rows} 条记录")
        
        # 重置自增ID
        cursor.execute("DELETE FROM sqlite_sequence")
        print("🔄 重置自增ID")
        
        # 重新启用外键约束检查
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # 提交更改
        conn.commit()
        
        # 验证清空结果
        print("\n📊 验证清空结果:")
        for table in tables:
            if table != 'sqlite_sequence':
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count} 条记录")
        
        print("\n✅ 数据库清空完成！")
        return True
        
    except Exception as e:
        print(f"❌ 清空数据库失败: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()
            print("🔒 数据库连接已关闭")

def backup_database(db_path: str = "tasks.db"):
    """备份数据库文件"""
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    try:
        backup_path = f"{db_path}.backup.{int(time.time())}"
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"💾 数据库已备份到: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ 备份数据库失败: {e}")
        return False

def main():
    """主函数"""
    print("🗄️  数据库清空工具")
    print("=" * 50)
    
    # 检查命令行参数
    db_path = "tasks.db"
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    print(f"目标数据库: {db_path}")
    
    # 询问是否备份
    backup_choice = input("\n是否在清空前备份数据库？(y/N): ").strip().lower()
    if backup_choice in ['y', 'yes']:
        if backup_database(db_path):
            print("✅ 备份完成")
        else:
            print("❌ 备份失败，是否继续？(y/N): ")
            if input().strip().lower() not in ['y', 'yes']:
                print("操作已取消")
                return
    
    # 确认清空操作
    print(f"\n⚠️  警告：此操作将清空数据库 {db_path} 中的所有数据！")
    confirm = input("确认要清空数据库吗？输入 'YES' 确认: ").strip()
    
    if confirm != 'YES':
        print("操作已取消")
        return
    
    # 执行清空操作
    if clear_database(db_path):
        print("\n🎉 数据库清空成功！")
    else:
        print("\n💥 数据库清空失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()
