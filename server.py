import json
import os
from io import BytesIO
import torch.cuda
import uvicorn
from pathlib import Path
from zipfile import ZipFile
from configparser import ConfigParser
from docx import Document
from typing import List
from docx.opc.exceptions import PackageNotFoundError
from fastapi import FastAPI, WebSocket, File, UploadFile, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from service.translate import translate_sentences, translate_folder_with_task_id
from utils.taskManager import task_manager, TaskStatus
from contextlib import asynccontextmanager
from models.model import *
from models.translateModel import TranslatorSingleton

# batch_translating: bool = False  # 批量翻译标志
config = ConfigParser()  # 创建配置解析器对象


@asynccontextmanager
async def lifespan(app: FastAPI):
    global accelerator
    config.read(os.path.abspath("./config/config.ini"))
    TranslatorSingleton.get_cpu_model()
    TranslatorSingleton.get_cuda_model()
    # 预加载tokenizer
    TranslatorSingleton._load_tokenizer("khk_Cyrl")
    TranslatorSingleton._load_tokenizer("eng_Latn")
    yield
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


# # 反馈批量翻译状态
# @app.get("/check_batch_translating")
# async def check_batch_translating():
#     return JSONResponse(content={"result": batch_translating})


# 上传文件
@app.post("/uploadfiles")
async def create_upload_files(request: Request, files: List[UploadFile] = File(...)):
    client_ip = request.client.host
    user_directory = os.path.join(os.path.abspath(config['DEFAULT']['UPLOAD_DIRECTORY']), client_ip)
    os.makedirs(user_directory, exist_ok=True)
    processed_files = []
    errors = []

    for file in files:
        if not file.filename.endswith('.docx'):
            errors.append(f"Unsupported file type: {file.filename}")
            continue

        try:
            # 从上传的文件创建BytesIO对象
            file_stream = BytesIO(await file.read())

            # 使用BytesIO对象加载DOCX文档
            document = Document(file_stream)

            # 生成新的文件名和位置
            new_file_location = os.path.join(user_directory, file.filename)

            # 将修改后的文档保存到本地
            document.save(new_file_location)
            processed_files.append(new_file_location)

        except Exception as e:
            errors.append(f"Error processing file {file.filename}: {str(e)}")
            continue
        finally:
            # 确保关闭文件流
            file_stream.close()

    if errors:
        return JSONResponse(status_code=500,
                            content={"message": "Errors occurred during file upload and processing", "errors": errors})
    return JSONResponse(status_code=200,
                        content={"message": f"Successfully uploaded and processed {len(processed_files)} files."})


# 批量翻译
@app.post("/translate/files", response_model=ResponseModel)
async def translate_files(request: Request, args: SourceRequest, background_tasks: BackgroundTasks):
    global batch_translating

    batch_translating = True
    client_ip = request.client.host
    user_directory = os.path.join(os.path.abspath(config['DEFAULT']['UPLOAD_DIRECTORY']), client_ip)
    output_dictionary = os.path.join(os.path.abspath(config['DEFAULT']['DOWNLOAD_DICTIONARY']), client_ip)
    try:
        task_manager.add_task(client_ip)
        background_tasks.add_task(translate_folder_with_task_id,
                                  task_id=client_ip,
                                  input_folder=user_directory,
                                  output_folder=output_dictionary,
                                  src_lang=args.source_lang,
                                  tgt_lang=args.target_lang
                                  )
    except PackageNotFoundError as ee:
        print(ee)
        raise HTTPException(status_code=501, detail=f"File not Found: {str(ee)}")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:

        batch_translating = False

    return JSONResponse(status_code=200, content={"success": True})


# websocket接口翻译文本
@app.websocket("/ws/translate/seq")
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
@app.get("/task_status/")
async def get_task_status(task_id: str):
    status = task_manager.get_task_status(task_id)
    if status == TaskStatus.COMPLETED:
        task_manager.delete_task(task_id)
    if status is None:
        return {"task_id": task_id, "result": "No Task"}
    return {"task_id": task_id, "result": status}


@app.get("/download-all")
async def download_all_files(requset: Request):
    client_ip = requset.client.host
    dir_path = Path(os.path.join(config['DEFAULT']['DOWNLOAD_DICTIONARY'], client_ip))
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
        return FileResponse(zip_path, filename="all_files.zip")
    else:
        raise HTTPException(status_code=404, detail="ZIP file creation failed")


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    uvicorn.run(app="server:app", host="127.0.0.1", port=8000, log_level="info", workers=1)
