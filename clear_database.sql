-- 数据库清空脚本
-- 用于清空所有任务管理相关的数据库表
-- 注意：此脚本会删除所有数据，请谨慎使用！

-- 设置外键约束检查为关闭（SQLite默认关闭）
PRAGMA foreign_keys = OFF;

-- 清空任务队列表
DELETE FROM task_queue;

-- 清空GPU状态表
DELETE FROM gpu_status;

-- 清空任务表
DELETE FROM tasks;

-- 重置自增ID（如果使用AUTOINCREMENT）
DELETE FROM sqlite_sequence WHERE name IN ('task_queue', 'gpu_status', 'tasks');

-- 重新设置外键约束检查
PRAGMA foreign_keys = ON;

-- 验证清空结果
SELECT 'task_queue' as table_name, COUNT(*) as record_count FROM task_queue
UNION ALL
SELECT 'gpu_status' as table_name, COUNT(*) as record_count FROM gpu_status
UNION ALL
SELECT 'tasks' as table_name, COUNT(*) as record_count FROM tasks;

-- 显示清空完成信息
SELECT '数据库清空完成！' as message;
