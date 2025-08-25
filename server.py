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
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from service.translate import translate_sentences, translate_folder_with_task_id
from utils.taskManager import task_manager, TaskStatus
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
    scheduler.add_job(task_manager.delete_downloaded_task_folders, 'cron', hour=12, minute=7,
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
@app.post("/translate/files")
async def translate_files(request: Request, args: SourceRequest, background_tasks: BackgroundTasks):
    # client_ip = args.client_ip
    client_ip = args.client_ip
    # 验证客户端ID格式，防止路径注入
    try:
        uuid.UUID(client_ip)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的客户端ID")
    
    user_directory = os.path.join(config_manager.get_upload_directory(), client_ip)
    # 修改：使用task_id作为下载目录名，而不是client_ip
    task_id = task_manager.create_task(metadata={"client_ip": client_ip})
    output_dictionary = os.path.join(config_manager.get_download_directory(), task_id)
    if os.path.exists(output_dictionary):
        delete_folder_contents(output_dictionary)
    try:
        # 使用异步方式检查任务数量
        import asyncio
        task_count = await asyncio.to_thread(task_manager.count_tasks)
        if task_count > config_manager.getint('SETTINGS', 'MAX_TASKS'):
            raise HTTPException(status_code=555, detail=f"服务器繁忙请稍后重试")
        background_tasks.add_task(translate_folder_with_task_id,
                                  task_id=task_id,
                                  input_folder=user_directory,
                                  output_folder=output_dictionary,
                                  src_lang=args.source_lang,
                                  tgt_lang=args.target_lang,
                                  via_eng=args.via_eng
                                  )
        logger.info(f"Successfully submit task from {client_ip}.")
    except PackageNotFoundError as ee:
        logger.error(f"{client_ip} translate files failed , {ee}.")
        raise HTTPException(status_code=501, detail=f"File not Found: {str(ee)}")
    except HTTPException as e:
        logger.error(f"{client_ip} translate files failed , {e}.")
        raise e
    except Exception as e:
        logger.error(f"{client_ip} translate files failed , {e}.")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

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
    status = task_manager.get_task_status(task_id)
    if status is None:
        return {"task_id": task_id, "result": "No Task"}
    
    # 只返回状态字符串，而不是整个状态对象
    if isinstance(status, dict) and 'status' in status:
        return {"task_id": task_id, "result": status['status']}
    else:
        return {"task_id": task_id, "result": str(status)}


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
        task_manager.update_task_status(task_id, TaskStatus.COMPLETED)
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
