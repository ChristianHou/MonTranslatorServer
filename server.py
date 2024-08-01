import json
import os
import uuid
import torch.cuda
import uvicorn
from utils.logging_config import logger
from pathlib import Path
from zipfile import ZipFile
from configparser import ConfigParser
from typing import List
from docx.opc.exceptions import PackageNotFoundError
from fastapi import FastAPI, WebSocket, File, UploadFile, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from service.translate import translate_sentences, translate_folder_with_task_id
from utils.taskManager import task_manager, TaskStatus
from utils.rateLimiter import rate_limiter, ws_rate_limiter
from utils.fileHandler import FileHandler
from contextlib import asynccontextmanager
from models.model import *
from models.translateModel import TranslatorSingleton
from utils.util import delete_folder_contents
from utils.cronjob import scheduler

config = ConfigParser()  # 创建配置解析器对象

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 预加载配置项
    config.read(os.path.abspath("./config/config.ini"))
    # 预加载模型
    TranslatorSingleton.initialize_models(num_cpu_models=1, num_cuda_models=2)
    # 预加载tokenizer
    TranslatorSingleton._load_tokenizer("khk_Cyrl")
    TranslatorSingleton._load_tokenizer("eng_Latn")
    # 定时任务
    scheduler.add_job(task_manager.delete_downloaded_task_folders, 'cron', hour=12, minute=7,
                      args=[config['DEFAULT']['DOWNLOAD_DICTIONARY']])
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


# 上传文件
@app.post("/uploadfiles")
@rate_limiter.limit()
async def create_upload_files(files: List[UploadFile] = File(...)):
    # client_ip = request.client.host
    client_ip = str(uuid.uuid4())
    user_directory = os.path.join(os.path.abspath(config['DEFAULT']['UPLOAD_DIRECTORY']), client_ip)
    try:
        FileHandler.process_files(user_directory, files)
        logger.info(f"Successfully uploaded and processed {len(files)} files from {client_ip}.")
    except HTTPException as e:
        logger.error(f"{client_ip} upload failed , {e.detail}.")
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})

    return JSONResponse(status_code=200,
                        content={"client_id": client_ip,
                                 "message": f"Successfully uploaded and processed {len(files)} files."})


# 批量翻译
@app.post("/translate/files")
async def translate_files(request: Request, args: SourceRequest, background_tasks: BackgroundTasks):
    # client_ip = request.client.host
    client_ip = args.client_ip
    user_directory = os.path.join(os.path.abspath(config['DEFAULT']['UPLOAD_DIRECTORY']), client_ip)
    output_dictionary = os.path.join(os.path.abspath(config['DEFAULT']['DOWNLOAD_DICTIONARY']), client_ip)
    if os.path.exists(output_dictionary):
        delete_folder_contents(output_dictionary)
    try:
        if task_manager.count_tasks() > int(config['DEFAULT']['MAX_TASKS']):
            raise HTTPException(status_code=555, detail=f"服务器繁忙请稍后重试")
        task_manager.add_task(client_ip)
        background_tasks.add_task(translate_folder_with_task_id,
                                  task_id=client_ip,
                                  input_folder=user_directory,
                                  output_folder=output_dictionary,
                                  src_lang=args.source_lang,
                                  tgt_lang=args.target_lang
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
        raise HTTPException(status_code=500, detail=f"An error occurred: {e.d}")

    return JSONResponse(status_code=200, content={"task_id": client_ip})


# websocket接口翻译文本
@app.websocket("/ws/translate/seq")
@ws_rate_limiter.limit()
async def websocket_translate(websocket: WebSocket):
    await websocket.accept()
    while True:
        # 接收客户端消息
        data = await websocket.receive_text()
        try:
            args = json.loads(data)
        except json.JSONDecodeError:
            await websocket.send_text(json.dumps({"error": "Invalid JSON format"}))
            continue

        sentences = args.get("sentences")
        result_data = translate_sentences(text=sentences, src_lang=args.get('source_lang'),
                                          tgt_lang=args.get('target_lang'))
        # 发送翻译结果给客户端
        await websocket.send_text(json.dumps({"result": result_data, "error": ''}))


# 获取任务状态的接口
@app.get("/task_status")
async def get_task_status(task_id: str):
    status = task_manager.get_task_status(task_id)
    if status is None:
        return {"task_id": task_id, "result": "No Task"}
    return {"task_id": task_id, "result": status}


@app.get("/download-all")
async def download_all_files(task_id: str):
    dir_path = Path(os.path.join(config['DEFAULT']['DOWNLOAD_DICTIONARY'], task_id))

    # 检查文件夹是否为空
    if not any(dir_path.iterdir()):
        raise HTTPException(status_code=404, detail="Directory is empty")

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
        task_manager.update_task_status(task_id, TaskStatus.DOWNLOADED)
        return FileResponse(zip_path, filename="all_files.zip")
    else:
        logger.error(f"Failed to download all files from {task_id}")
        raise HTTPException(status_code=404, detail="ZIP file creation failed")


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    uvicorn.run(app="server:app", host="127.0.0.1", port=8000, log_level="info", workers=1)
