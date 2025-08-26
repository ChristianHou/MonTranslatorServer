# 蒙语翻译服务器 - 任务管理功能

## 概述

本项目为蒙语翻译服务器添加了完整的任务管理功能，包括：

- **数据库持久化**: 使用SQLite数据库存储任务状态和队列信息
- **任务队列管理**: 智能的任务排队和GPU分配系统
- **实时状态更新**: 任务进度和状态的实时监控
- **Web管理界面**: 直观的任务管理Web界面
- **API接口**: 完整的RESTful API支持

## 功能特性

### 1. 任务状态管理
- **等待中 (pending)**: 任务已创建，等待GPU资源
- **处理中 (processing)**: 任务正在GPU上执行
- **已完成 (completed)**: 任务成功完成
- **失败 (failed)**: 任务执行失败
- **已取消 (cancelled)**: 任务被用户取消
- **超时 (timeout)**: 任务执行超时

### 2. 任务队列系统
- 基于优先级的任务排序
- 智能GPU资源分配
- 队列长度限制配置
- 自动任务调度

### 3. GPU负载均衡
- 实时GPU状态监控
- 内存使用率感知
- 任务类型感知分配
- 自动资源释放

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端界面      │    │   API接口       │    │   任务管理器    │
│  (Web页面)      │◄──►│  (FastAPI)      │◄──►│  (TaskManager)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   数据库        │    │   任务队列      │
                       │  (SQLite)       │    │  (QueueManager) │
                       └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   GPU监控       │    │   翻译引擎      │
                       │  (GPU Monitor)  │    │  (Translator)   │
                       └─────────────────┘    └─────────────────┘
```

## 安装和配置

### 1. 环境要求
- Python 3.8+
- SQLite 3
- CUDA支持（可选，用于GPU加速）

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置文件
在 `config/config.ini` 中添加任务管理相关配置：

```ini
[SETTINGS]
# 最大并发任务数
MAX_TASKS = 10
# 最大任务队列长度
MAX_TASK_QUEUE_SIZE = 50

[GPU]
# GPU实例数量
GPU_INSTANCES = 2
# GPU监控间隔（秒）
GPU_MONITOR_INTERVAL = 10
```

## 使用方法

### 1. 启动服务器
```bash
python start_server.py
```

### 2. 访问管理界面
- **任务管理页面**: http://localhost:8000/tasks
- **文件上传页面**: http://localhost:8000/
- **API文档**: http://localhost:8000/docs

### 3. API接口使用

#### 创建翻译任务
```bash
curl -X POST "http://localhost:8000/translate/files" \
     -H "Content-Type: application/json" \
     -d '{
       "client_ip": "user123",
       "source_lang": "mon_Cyrl",
       "target_lang": "cmn_Hans",
       "via_eng": false
     }'
```

#### 查询任务状态
```bash
curl "http://localhost:8000/task_status?task_id=task_uuid_here"
```

#### 获取任务列表
```bash
curl "http://localhost:8000/tasks?limit=20&status=pending"
```

#### 取消任务
```bash
curl -X POST "http://localhost:8000/tasks/task_uuid_here/cancel"
```

#### 重试任务
```bash
curl -X POST "http://localhost:8000/tasks/task_uuid_here/retry"
```

## 数据库结构

### 任务表 (tasks)
| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | TEXT | 任务唯一标识 |
| status | TEXT | 任务状态 |
| priority | INTEGER | 任务优先级 |
| created_at | TEXT | 创建时间 |
| started_at | TEXT | 开始时间 |
| completed_at | TEXT | 完成时间 |
| progress | REAL | 进度百分比 |
| error_message | TEXT | 错误信息 |
| client_ip | TEXT | 客户端IP |
| source_lang | TEXT | 源语言 |
| target_lang | TEXT | 目标语言 |
| via_eng | BOOLEAN | 是否通过英语 |
| file_count | INTEGER | 文件数量 |
| total_file_size | INTEGER | 总文件大小 |

### 任务队列表 (task_queue)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 自增ID |
| task_id | TEXT | 任务ID |
| priority | INTEGER | 优先级 |
| created_at | TEXT | 创建时间 |
| assigned_gpu | TEXT | 分配的GPU |
| assigned_at | TEXT | 分配时间 |

### GPU状态表 (gpu_status)
| 字段 | 类型 | 说明 |
|------|------|------|
| gpu_id | TEXT | GPU设备ID |
| device_name | TEXT | 设备名称 |
| memory_total | INTEGER | 总内存 |
| memory_used | INTEGER | 已用内存 |
| memory_free | INTEGER | 可用内存 |
| utilization | REAL | 使用率 |
| temperature | REAL | 温度 |
| is_available | BOOLEAN | 是否可用 |
| current_task_id | TEXT | 当前任务ID |

## 监控和调试

### 1. 日志文件
- 服务器日志: `logs/server.log`
- 任务管理日志: 控制台输出

### 2. 实时监控
- 任务状态实时更新
- GPU资源使用情况
- 队列状态监控

### 3. 性能指标
- 任务成功率统计
- 平均处理时间
- GPU利用率

## 故障排除

### 常见问题

#### 1. 任务卡在等待状态
- 检查GPU是否可用
- 查看GPU内存使用情况
- 检查任务队列状态

#### 2. 数据库连接失败
- 检查SQLite文件权限
- 确认数据库文件路径
- 检查磁盘空间

#### 3. GPU分配失败
- 检查CUDA驱动
- 查看GPU状态
- 重启GPU监控服务

### 调试命令
```bash
# 查看任务统计
curl "http://localhost:8000/task_metrics"

# 查看队列状态
curl "http://localhost:8000/queue_status"

# 查看GPU状态
curl "http://localhost:8000/gpu_status"
```

## 扩展和定制

### 1. 添加新的任务类型
在 `utils/persistent_task_manager.py` 中扩展任务类型支持。

### 2. 自定义GPU分配策略
在 `utils/task_queue_manager.py` 中修改 `_select_best_gpu` 方法。

### 3. 添加新的监控指标
在相应的管理器中添加新的统计方法。

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件
- 项目讨论区

---

**注意**: 本任务管理系统为生产环境设计，包含完整的错误处理、日志记录和监控功能。建议在生产环境中使用前进行充分测试。
