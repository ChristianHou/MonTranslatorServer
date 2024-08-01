import os
from transformers import (
    AutoTokenizer,
)
import ctranslate2 as ct2
from utils.logging_config import logger
from pathlib import Path


def load_ct2_model_tokenizer(
        model_path: str,
        tokenizer_path: str,
        src_lang: str,
        device: str = "cpu",
):
    translator = ct2.Translator(model_path, device=device)
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, src_lang=src_lang)
    return translator, tokenizer


def delete_folder_contents(folder_path):
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            delete_folder_contents(file_path)
            os.rmdir(file_path)


def delete_folder(folder_path: Path):
    """删除文件夹中的所有内容"""
    for item in folder_path.iterdir():
        if item.is_dir():
            delete_folder_contents(item)
            item.rmdir()
        else:
            item.unlink()


def delete_download_folder():
    logger.info("Deleting download folder contents...")
    delete_folder_contents(Path("./files/download"))
    logger.info("Download folder contents deleted.")
