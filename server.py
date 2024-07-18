import json
import os
from io import BytesIO
import uvicorn
from accelerate import Accelerator
from docx import Document
from typing import List

from docx.opc.exceptions import PackageNotFoundError
from fastapi import FastAPI, WebSocket, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from translate import check_or_load_model, translate_2_zh, translate_sentences
from utils.util import delete_folder_contents


# 请求基础模型
class SourceRequest(BaseModel):
    sentences: str | None = None
    sentences_path: str = None
    sentences_dir: str = None
    output_path: str = './sample_text/result.txt'
    files_extension: str = "txt"
    source_lang: str = None
    target_lang: str = None
    starting_batch_size: int = 4
    model_name_or_path: str = None
    lora_weights_name_or_path: str = None
    max_length: int = 1024
    num_beams: int = 5
    precision: str = None
    do_sample: bool = False
    temperature: float = 0.8
    top_k: int = 100
    top_p: float = 0.75
    repetition_penalty: float = 1.0
    keep_special_tokens: bool = False
    keep_tokenization_spaces: bool = False
    num_return_sequences: int = 1
    force_auto_device_map: bool = False
    prompt: str = None
    trust_remote_code: bool = False


class ResponseModel(BaseModel):
    result: str


batch_translating: bool = False  # 批量翻译标志
model_list = {}  # 模型列表
file_path = './model_map.json'  # 模型映射表
accelerator = None
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)


# 启动函数，初始化模型列表和模型
@app.on_event("startup")
async def startup_event():
    global model_list,accelerator
    try:
        accelerator = Accelerator()
        with open(file_path, 'r') as file:
            model_list = json.load(file)
        print("Contents of the file:", model_list)
        check_or_load_model(model_list['facebook/nllb-200-1.3B'],
                            quantization=None,
                            lora_weights_name_or_path=None,
                            dtype=None,
                            force_auto_device_map=False,
                            trust_remote_code=False,
                            accelerator=accelerator
                            )
        print(model_list)
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file {file_path}.")


# 设置文件存储的目录
UPLOAD_DIRECTORY = os.path.abspath("./uploaded/files")


# 反馈批量翻译状态
@app.get("/check_batch_translating")
async def check_batch_translating():
    return JSONResponse(content={"result": batch_translating})


# 上传文件
@app.post("/uploadfiles")
async def create_upload_files(files: List[UploadFile] = File(...)):
    os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
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
            new_file_location = os.path.join(UPLOAD_DIRECTORY, file.filename)

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
async def translate_files(args: SourceRequest):
    global model_list, batch_translating
    model_name = model_list[args.model_name_or_path]
    if model_name is None:
        return JSONResponse(status_code=400, content={"error": "Wrong model name!"})

    batch_translating = True

    try:
        translate_2_zh(
            sentences_path=args.sentences_path,
            sentences_dir=UPLOAD_DIRECTORY,
            files_extension=args.files_extension,
            output_path=args.output_path,
            source_lang=args.source_lang,
            target_lang=args.target_lang,
            starting_batch_size=args.starting_batch_size,
            model_name_or_path=model_name,
            max_length=args.max_length,
            num_beams=args.num_beams,
            num_return_sequences=args.num_return_sequences,
            precision=args.precision,
            do_sample=args.do_sample,
            temperature=args.temperature,
            top_k=args.top_k,
            top_p=args.top_p,
            straight_translate=True if args.model_name_or_path == "facebook/nllb-200-3.3B" or args.model_name_or_path.endswith("3.3B") else False,
            switch_model_en_2_zh=False if args.model_name_or_path.startswith("(推荐)") else True
        )
    except PackageNotFoundError as ee:
        print(ee)
        raise HTTPException(status_code=501, detail=f"File not Found: {str(ee)}")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        delete_folder_contents(UPLOAD_DIRECTORY)
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

        global model_list
        model_name = model_list.get(args.get("model_name"))
        if model_name is None:
            await websocket.send_text(json.dumps({"error": "Wrong model name!"}))
            continue

        sentences = args.get("sentences")

        tmp_translated_sentences = translate_sentences(
            sentences=sentences,
            source_lang=args.get('source_lang'),
            target_lang="eng_Latn",
            model_name_or_path=model_name
        )
        result_data = translate_sentences(
            sentences=tmp_translated_sentences,
            source_lang="eng_Latn",
            target_lang=args.get('target_lang'),
            model_name_or_path=model_name
        )

        # 发送翻译结果给客户端
        await websocket.send_text(json.dumps({"result": result_data, "error": ''}))


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    uvicorn.run(app="server:app", host="127.0.0.1", port=8000, log_level="info", workers=1)
