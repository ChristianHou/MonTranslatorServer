import os
from utils.util import delete_folder_contents
from utils.persistent_task_manager import persistent_task_manager, TaskStatus
from models.translateModel import TranslatorSingleton, DocxTranslator, TableTranslator


def encode_string(text):
    return text.replace("\r", r"\r").replace("\n", r"\n").replace("\t", r"\t")


# 翻译函数，接受text、src_lang和tgt_lang参数
def translate_sentences(text: str, src_lang: str, tgt_lang: str, via_eng: bool):
    texts = text.split("\n")
    translated_texts = TranslatorSingleton.translate_batch(texts=texts,
                                                           src_lang=src_lang,
                                                           tgt_lang=tgt_lang,
                                                           use_cuda=True,
                                                           via_eng=via_eng,
                                                           task_type="text")  # 文本翻译任务
    return '\n'.join(translated_texts)


# 翻译文件夹中的所有docx文件
def translate_folder(input_folder: str, output_folder: str, src_lang: str, tgt_lang: str, via_eng: bool = False):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 获取所有支持的文件类型
    supported_extensions = {'.docx', '.xlsx', '.xls', '.csv'}
    
    # 批量处理文件，提高效率
    files_to_process = []
    for filename in os.listdir(input_folder):
        if any(filename.lower().endswith(ext) for ext in supported_extensions):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, f"translated_{filename}")
            files_to_process.append((input_path, output_path, filename))
        else:
            print(f"Unsupported file type: {filename}")
    
    # 按文件类型分组处理，减少重复的模型加载
    for input_path, output_path, filename in files_to_process:
        try:
            if filename.lower().endswith('.docx'):
                DocxTranslator.translate_docx(input_path=input_path,
                                              output_path=output_path,
                                              src_lang=src_lang,
                                              tgt_lang=tgt_lang,
                                              via_eng=via_eng)
            elif filename.lower().endswith(('.xlsx', '.xls')):
                TableTranslator.translate_excel(input_path=input_path,
                                                output_path=output_path,
                                                src_lang=src_lang,
                                                tgt_lang=tgt_lang,
                                                via_eng=via_eng)
            elif filename.lower().endswith('.csv'):
                TableTranslator.translate_csv(input_path=input_path,
                                              output_path=output_path,
                                              src_lang=src_lang,
                                              tgt_lang=tgt_lang,
                                              via_eng=via_eng)
            
            print(f"Translated {input_path} to {output_path}")
        except Exception as e:
            print(f"Failed to translate {filename}: {e}")
            # 继续处理其他文件，不中断整个流程


# 带有task_id的翻译文件夹函数
def translate_folder_with_task_id(task_id: str, input_folder: str, output_folder: str, src_lang: str, tgt_lang: str,
                                  via_eng: bool = False):
    success = False
    try:
        # 更新任务状态为处理中
        persistent_task_manager.update_task_status(task_id, TaskStatus.PROCESSING, progress=25)
        
        translate_folder(input_folder=input_folder,
                         output_folder=output_folder,
                         src_lang=src_lang,
                         tgt_lang=tgt_lang,
                         via_eng=via_eng)
        
        # 更新任务状态为已完成
        persistent_task_manager.update_task_status(task_id, TaskStatus.COMPLETED, progress=100)
        success = True
        
    except Exception as e:
        # 记录详细错误信息
        import traceback
        error_details = traceback.format_exc()
        print(f"Translation failed for task {task_id}: {error_details}")
        
        # 更新任务状态为失败
        persistent_task_manager.update_task_status(task_id, TaskStatus.FAILED, error_message=str(e))
        
        # 重新抛出异常
        raise e
        
    finally:
        # 只有在成功时才删除输入文件夹，失败时保留以便调试和重试
        if success:
            try:
                # 确保输出文件夹存在且包含翻译后的文件
                if os.path.exists(output_folder) and any(os.listdir(output_folder)):
                    delete_folder_contents(input_folder)
                    os.rmdir(input_folder)
                    print(f"Successfully cleaned up input folder: {input_folder}")
                else:
                    print(f"Warning: Output folder is empty or doesn't exist, keeping input folder: {input_folder}")
            except OSError as e:
                print(f"Warning: Failed to cleanup input folder {input_folder}: {e}")
                # 不抛出异常，避免影响任务状态更新
