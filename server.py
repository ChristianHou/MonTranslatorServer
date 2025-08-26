import json
import os
import uuid
import torch.cuda
import uvicorn
from utils.logging_config import logger
from pathlib import Path
from zipfile import ZipFile
from typing import List
from docx.opc.exceptions import PackageNotFoundError
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from service.translate import translate_sentences, translate_folder_with_task_id
from utils.persistent_task_manager import persistent_task_manager, TaskStatus
from utils.rateLimiter import rate_limiter
from utils.fileHandler import FileHandler
from contextlib import asynccontextmanager
from models.model import *
from models.translateModel import TranslatorSingleton
from utils.util import delete_folder_contents
from utils.cronjob import scheduler
from utils.config_manager import config_manager
import time
import logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 从配置文件读取GPU和CPU实例数量
    num_cpu_models = config_manager.getint('GPU', 'CPU_INSTANCES', 2)
    num_gpu_models = config_manager.getint('GPU', 'GPU_INSTANCES', 4)
    
    # 预加载模型
    TranslatorSingleton.initialize_models(num_cpu_models=num_cpu_models, num_gpu_models=num_gpu_models)
    
    # 预加载tokenizer（添加错误处理）
    try:
        TranslatorSingleton._load_tokenizer("khk_Cyrl")
        logging.info("✅ khk_Cyrl tokenizer 加载成功")
    except Exception as e:
        logging.warning(f"⚠️  khk_Cyrl tokenizer 加载失败: {e}")
    
    try:
        TranslatorSingleton._load_tokenizer("eng_Latn")
        logging.info("✅ eng_Latn tokenizer 加载成功")
    except Exception as e:
        logging.warning(f"⚠️  eng_Latn tokenizer 加载失败: {e}")
    
    # 定时任务
    scheduler.add_job(persistent_task_manager.delete_downloaded_task_folders, 'cron', hour=12, minute=7,
                      args=[config_manager.get_download_directory()])
    scheduler.start()
    yield
    scheduler.shutdown()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

# 挂载静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

# 根路由 - 提供首页
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """提供首页HTML文件"""
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        # 如果templates目录下没有文件，尝试根目录的旧文件
        try:
            with open("index.html", "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read(), status_code=200)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="首页文件未找到")


# 任务管理页面路由
@app.get("/tasks", response_class=HTMLResponse)
async def task_management_page():
    """提供任务管理页面HTML文件"""
    try:
        with open("templates/task_management.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="任务管理页面文件未找到")

# 测试页面路由
@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """提供测试页面HTML文件"""
    try:
        with open("test_upload_simple.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="测试页面文件未找到")

# 简单文件上传测试端点
@app.post("/test_upload")
async def test_upload_simple(file: UploadFile = File(...)):
    """简单的文件上传测试端点"""
    try:
        logger.info(f"测试上传开始: {file.filename}")
        
        # 创建测试目录
        test_dir = "test_upload"
        os.makedirs(test_dir, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(test_dir, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"测试文件保存成功: {file_path}")
        
        return {"message": "测试上传成功", "filename": file.filename}
        
    except Exception as e:
        logger.error(f"测试上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"测试上传失败: {str(e)}")

# 简单测试页面路由
@app.get("/simple_test", response_class=HTMLResponse)
async def simple_test_page():
    """提供简单测试页面HTML文件"""
    try:
        with open("test_simple_upload.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="简单测试页面文件未找到")

# Favicon路由（可选）
@app.get("/favicon.ico")
async def favicon():
    """返回favicon，避免404错误"""
    raise HTTPException(status_code=404, detail="Favicon not found")


# 上传文件
@app.post("/uploadfiles")
@rate_limiter.limit()
async def create_upload_files(files: List[UploadFile] = File(...)):
    # client_ip = request.client.host
    # 使用安全的UUID生成，避免路径注入
    client_ip = str(uuid.uuid4())
    # 验证UUID格式，防止恶意输入
    try:
        uuid.UUID(client_ip)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的客户端ID")
    
    # 验证文件大小
    max_file_size = config_manager.getint('SETTINGS', 'MAX_FILE_SIZE', 10485760)  # 10MB
    total_size = 0
    
    for file in files:
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        # 检查文件大小
        try:
            # 读取文件内容以获取实际大小
            content = await file.read()
            file_size = len(content)
            total_size += file_size
            
            if file_size > max_file_size:
                raise HTTPException(
                    status_code=413, 
                    detail=f"文件 {file.filename} 过大: {file_size / 1024 / 1024:.1f}MB，最大允许: {max_file_size / 1024 / 1024:.1f}MB"
                )
            
            # 重置文件指针，以便后续处理
            await file.seek(0)
            
        except Exception as e:
            logger.error(f"文件大小验证失败: {e}")
            raise HTTPException(status_code=400, detail=f"文件验证失败: {str(e)}")
    
    logger.info(f"文件上传开始: {len(files)} 个文件，总大小: {total_size / 1024 / 1024:.2f}MB")
    
    user_directory = os.path.join(config_manager.get_upload_directory(), client_ip)
    try:
        FileHandler.process_files(user_directory, files)
        logger.info(f"Successfully uploaded and processed {len(files)} files from {client_ip}.")
    except HTTPException as e:
        logger.error(f"{client_ip} upload failed , {e.detail}.")
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        logger.error(f"{client_ip} upload failed with unexpected error: {e}")
        return JSONResponse(status_code=500, content={"message": f"文件处理失败: {str(e)}"})

    return JSONResponse(status_code=200,
                        content={"client_id": client_ip,
                                 "message": f"Successfully uploaded and processed {len(files)} files."})


# 批量翻译
# 新增任务提交接口（不再处理文件上传）
@app.post("/submit_translation_task")
async def submit_translation_task(
    background_tasks: BackgroundTasks,
    client_id: str = Form(...),
    source_lang: str = Form(...),
    target_lang: str = Form(...),
    via_eng: bool = Form(False)
):
    # 验证客户端ID
    try:
        uuid.UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的客户端ID")
    
    # 验证语言设置
    if not source_lang or not target_lang:
        raise HTTPException(status_code=400, detail="请指定源语言和目标语言")
    
    if source_lang == target_lang:
        raise HTTPException(status_code=400, detail="源语言和目标语言不能相同")
    
    # 获取已上传的文件目录
    user_directory = os.path.join(config_manager.get_upload_directory(), client_id)
    if not os.path.exists(user_directory):
        raise HTTPException(status_code=404, detail="找不到上传的文件，请先上传文件")
    
    # 获取目录中的文件
    try:
        filenames = os.listdir(user_directory)
        if not filenames:
            raise HTTPException(status_code=400, detail="上传目录中没有文件")
    except Exception as e:
        logger.error(f"读取上传文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"读取上传文件失败: {str(e)}")
    
    # 计算文件总大小
    total_size = 0
    file_count = len(filenames)
    for filename in filenames:
        file_path = os.path.join(user_directory, filename)
        total_size += os.path.getsize(file_path)
    
    # 创建翻译任务
    try:
        task_id = persistent_task_manager.create_task(
            metadata={"client_ip": client_id, "filenames": filenames},
            client_ip=client_id,
            source_lang=source_lang,
            target_lang=target_lang,
            via_eng=via_eng,
            file_count=file_count,
            total_file_size=total_size
        )
    except Exception as e:
        logger.error(f"创建翻译任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建翻译任务失败: {str(e)}")
    
    # 设置输出目录
    output_directory = os.path.join(config_manager.get_download_directory(), task_id)
    if os.path.exists(output_directory):
        delete_folder_contents(output_directory)
    
    try:
        # 检查任务数量
        import asyncio
        task_count = await asyncio.to_thread(persistent_task_manager.count_tasks)
        if task_count > config_manager.getint('SETTINGS', 'MAX_TASKS'):
            raise HTTPException(status_code=555, detail="服务器繁忙请稍后重试")
        
        # 添加后台任务
        background_tasks.add_task(translate_folder_with_task_id,
                                  task_id=task_id,
                                  input_folder=user_directory,
                                  output_folder=output_directory,
                                  src_lang=source_lang,
                                  tgt_lang=target_lang,
                                  via_eng=via_eng
                                  )
        logger.info(f"成功提交翻译任务: client_id={client_id}, task_id={task_id}")
    except PackageNotFoundError as ee:
        logger.error(f"翻译任务失败: {ee}")
        raise HTTPException(status_code=501, detail=f"文件未找到: {str(ee)}")
    except HTTPException as e:
        logger.error(f"翻译任务失败: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"翻译任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"发生错误: {str(e)}")

    return JSONResponse(status_code=200, content={"task_id": task_id})


# HTTP接口翻译文本
@app.post("/translate/text")
@rate_limiter.limit()
async def translate_text(request: Request, args: SourceRequest):
    """文本翻译接口 - 支持实时翻译"""
    try:
        if not args.sentences or not args.sentences.strip():
            raise HTTPException(status_code=400, detail="请输入要翻译的文本")
        
        if not args.source_lang or not args.target_lang:
            raise HTTPException(status_code=400, detail="请指定源语言和目标语言")
        
        if args.source_lang == args.target_lang:
            raise HTTPException(status_code=400, detail="源语言和目标语言不能相同")
        
        # 执行翻译
        result_data = translate_sentences(
            text=args.sentences, 
            src_lang=args.source_lang,
            tgt_lang=args.target_lang, 
            via_eng=args.via_eng or False
        )
        
        logger.info(f"Text translation completed for {len(args.sentences)} characters")
        return JSONResponse(
            status_code=200, 
            content={"result": result_data, "error": "", "status": "success"}
        )
        
    except Exception as e:
        logger.error(f"Text translation failed: {str(e)}")
        return JSONResponse(
            status_code=500, 
            content={"result": "", "error": str(e), "status": "error"}
        )


# 获取任务状态的接口
@app.get("/task_status")
async def get_task_status(task_id: str):
    status = persistent_task_manager.get_task_status(task_id)
    if status is None:
        return {"task_id": task_id, "result": "No Task"}
    
    # 返回完整的任务状态信息
    return {
        "task_id": task_id,
        "result": status.get('status', 'unknown'),
        "progress": status.get('progress', 0.0),
        "created_at": status.get('created_at'),
        "started_at": status.get('started_at'),
        "completed_at": status.get('completed_at'),
        "error_message": status.get('error_message'),
        "client_ip": status.get('client_ip'),
        "source_lang": status.get('source_lang'),
        "target_lang": status.get('target_lang'),
        "via_eng": status.get('via_eng'),
        "file_count": status.get('file_count'),
        "total_file_size": status.get('total_file_size')
    }


@app.get("/download-all")
async def download_all_files(task_id: str):
    # 验证任务ID格式，防止路径注入
    try:
        uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的任务ID")
    
    dir_path = Path(os.path.join(config_manager.get_download_directory(), task_id))

    # 检查目录是否存在
    if not dir_path.exists():
        raise HTTPException(status_code=404, detail="下载目录不存在，任务可能尚未完成或已过期")
    
    # 检查文件夹是否为空
    try:
        if not any(dir_path.iterdir()):
            raise HTTPException(status_code=404, detail="下载目录为空，没有可下载的文件")
    except PermissionError:
        raise HTTPException(status_code=500, detail="无法访问下载目录，权限不足")

    zip_path = dir_path / "all_files.zip"

    # 清理之前的zip文件
    if zip_path.exists():
        zip_path.unlink()

    # 创建新的zip文件
    with ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = Path(root) / file
                zipf.write(file_path, file_path.relative_to(dir_path))

    if zip_path.exists():
        logger.info(f"Successfully downloaded all files from {task_id}")
        # 使用COMPLETED状态，因为DOWNLOADED不是有效的TaskStatus
        persistent_task_manager.update_task_status(task_id, TaskStatus.COMPLETED)
        return FileResponse(zip_path, filename="all_files.zip")
    else:
        logger.error(f"Failed to download all files from {task_id}")
        raise HTTPException(status_code=404, detail="ZIP file creation failed")


@app.get("/gpu_status")
async def get_gpu_status():
    """获取GPU状态信息"""
    try:
        from models.translateModel import TranslatorSingleton
        gpu_status = TranslatorSingleton.get_gpu_status()
        return gpu_status
    except Exception as e:
        logger.error(f"获取GPU状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取GPU状态失败: {e}")

@app.get("/system_info")
async def get_system_info():
    """获取系统信息"""
    try:
        import psutil
        import platform
        
        # CPU信息
        cpu_info = {
            "count": psutil.cpu_count(),
            "percent": psutil.cpu_percent(interval=1),
            "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
        
        # 内存信息
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used
        }
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        disk_info = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }
        
        # 系统信息
        system_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        }
        
        return {
            "cpu": cpu_info,
            "memory": memory_info,
            "disk": disk_info,
            "system": system_info,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统信息失败: {e}")


@app.get("/tasks")
async def get_all_tasks(limit: int = 50, status:str = None):
    """获取所有任务列表"""
    try:
        from utils.persistent_task_manager import TaskStatus
        
        status_filter = None
        if status:
            try:
                status_filter = TaskStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的任务状态: {status}")
        
        tasks = persistent_task_manager.get_all_tasks(status_filter=status_filter, limit=limit)
        return {"tasks": tasks, "total": len(tasks)}
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {e}")


@app.get("/task_metrics")
async def get_task_metrics():
    """获取任务统计指标"""
    try:
        metrics = persistent_task_manager.get_task_metrics()
        return metrics
        
    except Exception as e:
        logger.error(f"获取任务统计指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务统计指标失败: {e}")


@app.get("/queue_status")
async def get_queue_status():
    """获取任务队列状态"""
    try:
        from utils.task_queue_manager import task_queue_manager
        status = task_queue_manager.get_queue_status()
        return status
        
    except Exception as e:
        logger.error(f"获取队列状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取队列状态失败: {e}")


@app.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str, reason: str = "用户取消"):
    """取消任务"""
    try:
        success = persistent_task_manager.cancel_task(task_id, reason)
        if success:
            return {"message": "任务取消成功", "task_id": task_id}
        else:
            raise HTTPException(status_code=400, detail="任务取消失败")
            
    except Exception as e:
        logger.error(f"取消任务失败: {task_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"取消任务失败: {e}")


@app.post("/tasks/{task_id}/retry")
async def retry_task(task_id: str):
    """重试任务"""
    try:
        success = persistent_task_manager.retry_task(task_id)
        if success:
            return {"message": "任务重试成功", "task_id": task_id}
        else:
            raise HTTPException(status_code=400, detail="任务重试失败")
            
    except Exception as e:
        logger.error(f"重试任务失败: {task_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"重试任务失败: {e}")


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    try:
        # 这里可以添加删除逻辑，或者只是标记为删除
        # 暂时返回成功，实际删除逻辑需要根据业务需求实现
        return {"message": "任务删除成功", "task_id": task_id}
        
    except Exception as e:
        logger.error(f"删除任务失败: {task_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"删除任务失败: {e}")


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    # 设置5分钟超时时间 (300秒)
    uvicorn.run(
        app="server:app", 
        host="0.0.0.0", 
        port=8000, 
        log_level="info", 
        workers=1,
        timeout_keep_alive=300,  # 5分钟超时
        timeout_graceful_shutdown=30
    )
