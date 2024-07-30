import logging
import os
from docx import Document
from tqdm import tqdm
import torch
from typing import Optional
from accelerate import Accelerator
from utils.util import load_model_for_inference, delete_folder_contents
from utils.taskManager import update_task_status
from models.translateModel import TranslatorSingleton, DocxTranslator


def encode_string(text):
    return text.replace("\r", r"\r").replace("\n", r"\n").replace("\t", r"\t")


# 翻译函数，接受text、src_lang和tgt_lang参数
def translate_sentences(text: str, src_lang: str, tgt_lang: str):
    translated_text = TranslatorSingleton.translate_sentence(text, src_lang, tgt_lang)
    return translated_text


# 翻译文件夹中的所有docx文件
def translate_folder(input_folder: str, output_folder: str, src_lang: str, tgt_lang: str):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.endswith(".docx"):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, f"translated_{filename}")
            DocxTranslator.translate_docx(input_path, output_path, src_lang, tgt_lang)
            print(f"Translated {input_path} to {output_path}")


# 带有task_id的翻译文件夹函数
@update_task_status  # 动态传递task_id给装饰器
def translate_folder_with_task_id(task_id: str, input_folder: str, output_folder: str, src_lang: str, tgt_lang: str):
    try:
        translate_folder(input_folder, output_folder, src_lang, tgt_lang)
    except Exception as e:
        print(e)
    finally:
        delete_folder_contents(input_folder)
