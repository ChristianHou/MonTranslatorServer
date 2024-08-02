import os
from utils.util import delete_folder_contents
from utils.taskManager import update_task_status
from models.translateModel import TranslatorSingleton, DocxTranslator, TableTranslator


def encode_string(text):
    return text.replace("\r", r"\r").replace("\n", r"\n").replace("\t", r"\t")


# 翻译函数，接受text、src_lang和tgt_lang参数
def translate_sentences(text: str, src_lang: str, tgt_lang: str, via_eng: bool):
    texts = text.split("\n")
    translated_texts = TranslatorSingleton.translate_batch(texts=texts,
                                                           src_lang=src_lang,
                                                           tgt_lang=tgt_lang,
                                                           via_eng=via_eng)
    return '\n'.join(translated_texts)


# 翻译文件夹中的所有docx文件
def translate_folder(input_folder: str, output_folder: str, src_lang: str, tgt_lang: str, via_eng: bool = False):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, f"translated_{filename}")

        if filename.endswith(".docx"):
            DocxTranslator.translate_docx(input_path=input_path,
                                          output_path=output_path,
                                          src_lang=src_lang,
                                          tgt_lang=tgt_lang,
                                          via_eng=via_eng)
        elif filename.endswith((".xlsx", ".xls")):
            TableTranslator.translate_excel(input_path=input_path,
                                            output_path=output_path,
                                            src_lang=src_lang,
                                            tgt_lang=tgt_lang,
                                            via_eng=via_eng)
        elif filename.endswith(".csv"):
            TableTranslator.translate_csv(input_path=input_path,
                                          output_path=output_path,
                                          src_lang=src_lang,
                                          tgt_lang=tgt_lang,
                                          via_eng=via_eng)

        print(f"Translated {input_path} to {output_path}")


# 带有task_id的翻译文件夹函数
@update_task_status  # 动态传递task_id给装饰器
def translate_folder_with_task_id(task_id: str, input_folder: str, output_folder: str, src_lang: str, tgt_lang: str,
                                  via_eng: bool = False):
    try:
        translate_folder(input_folder=input_folder,
                         output_folder=output_folder,
                         src_lang=src_lang,
                         tgt_lang=tgt_lang,
                         via_eng=via_eng)
    except Exception as e:
        print(e)
    finally:
        delete_folder_contents(input_folder)
        os.rmdir(input_folder)
