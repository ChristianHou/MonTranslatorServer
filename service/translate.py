import logging
import os
from docx import Document
from tqdm import tqdm
import torch
from typing import Optional
from accelerate import Accelerator
from utils.util import load_model_for_inference, delete_folder_contents
from utils.taskManager import update_task_status

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
MODEL_NAME_OR_PATH = ""
MY_MODEL = None
MY_TOKENIZER = None
TMP_FOLDER = os.path.abspath("../tmp_folder")


def encode_string(text):
    return text.replace("\r", r"\r").replace("\n", r"\n").replace("\t", r"\t")


def check_or_load_model(model_name_or_path, quantization, lora_weights_name_or_path, dtype, force_auto_device_map,
                        trust_remote_code, accelerator):
    global MODEL_NAME_OR_PATH, MY_MODEL, MY_TOKENIZER
    if MODEL_NAME_OR_PATH != model_name_or_path:
        MY_TOKENIZER = None
        MY_MODEL = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        MY_MODEL, MY_TOKENIZER = load_model_for_inference(
            weights_path=model_name_or_path,
            quantization=quantization,
            lora_weights_name_or_path=lora_weights_name_or_path,
            torch_dtype=dtype,
            force_auto_device_map=force_auto_device_map,
            trust_remote_code=trust_remote_code,
        )
        MY_MODEL.to(accelerator.device)
        MODEL_NAME_OR_PATH = model_name_or_path


def translate_sentences(sentences: str,
                        source_lang: str,
                        target_lang: str,
                        model_name_or_path: str = "facebook/m2m100_1.2B",
                        max_length: int = 1024,
                        num_beams: int = 4,
                        do_sample: bool = False,
                        temperature: float = 1.0,
                        top_k: int = 50,
                        top_p: float = 1.0,
                        accelerator: Accelerator = None,
                        ):
    global MODEL_NAME_OR_PATH, MY_MODEL, MY_TOKENIZER
    # Prepare the text for translation
    # Initialize the Accelerator
    if accelerator is None:
        accelerator = Accelerator()

    # Load the translation model and tokenizer
    check_or_load_model(model_name_or_path,
                        quantization=None,
                        lora_weights_name_or_path=None,
                        dtype=None,
                        force_auto_device_map=False,
                        trust_remote_code=False,
                        accelerator=accelerator)

    # Configure translation settings
    gen_kwargs = {
        "max_length": max_length,
        "num_beams": num_beams,
        "do_sample": do_sample,
        "temperature": temperature,
        "top_k": top_k,
        "top_p": top_p
    }

    if source_lang:
        MY_TOKENIZER.src_lang = source_lang

    if target_lang:
        lang_code_to_idx = MY_TOKENIZER.lang_code_to_id.get(target_lang, None)
        if lang_code_to_idx is None:
            raise ValueError(f"Target language {target_lang} not supported by the tokenizer.")
        gen_kwargs["forced_bos_token_id"] = lang_code_to_idx

    # translate
    sentences_list = sentences.split('\n')
    translated_sentences = []
    for seq in sentences_list:
        if not seq.strip():
            translated_sentences.append('')

        inputs = MY_TOKENIZER(seq, return_tensors="pt", max_length=gen_kwargs["max_length"], truncation=True)
        inputs = {k: v.to(accelerator.device) for k, v in inputs.items()}

        with torch.no_grad():
            generated_tokens = MY_MODEL.generate(**inputs, **gen_kwargs)

        # Decode the translation
        translated_sentence = MY_TOKENIZER.decode(generated_tokens[0], skip_special_tokens=True)
        translated_sentences.append(translated_sentence)

    return '\n'.join(translated_sentences)


def translate_run(run, gen_kwargs, accelerator):
    global MODEL_NAME_OR_PATH, MY_MODEL, MY_TOKENIZER
    # Prepare the text for translation
    if not run.text.strip():
        return ""

    inputs = MY_TOKENIZER(run.text, return_tensors="pt", max_length=gen_kwargs["max_length"], truncation=True)
    inputs = {k: v.to(accelerator.device) for k, v in inputs.items()}

    with torch.no_grad():
        generated_tokens = MY_MODEL.generate(**inputs, **gen_kwargs)

    # Decode the translation
    translated_sentence = MY_TOKENIZER.decode(generated_tokens[0], skip_special_tokens=True)

    return translated_sentence


def translate_paragraph(paragraph, gen_kwargs, accelerator):
    translated_runs = []

    for run in paragraph.runs:
        translated_text = translate_run(run, gen_kwargs, accelerator)
        translated_runs.append((translated_text, run))

    paragraph.clear()

    for translated_text, original_run in translated_runs:
        translated_run = paragraph.add_run(translated_text)

        translated_run.bold = original_run.bold
        translated_run.italic = original_run.italic
        translated_run.underline = original_run.underline
        translated_run.font.size = original_run.font.size
        translated_run.font.name = original_run.font.name
        translated_run.font.color.rgb = original_run.font.color.rgb
        translated_run.font.highlight_color = original_run.font.highlight_color


def translate_docx_file(file_path, output_path, gen_kwargs, accelerator):
    # Open the .docx file
    doc = Document(file_path)

    # Translate each paragraph using Accelerator
    for para in tqdm(doc.paragraphs, desc=f"Translating {file_path}"):
        if para.text.strip():
            translate_paragraph(para, gen_kwargs, accelerator)

    # Save the modified document
    doc.save(output_path)


def translate_folder(folder_path: str,
                     output_folder: str,
                     source_lang: str,
                     target_lang: str,
                     model_name_or_path: str,
                     accelerator: Accelerator = None,
                     gen_kwargs: dict = None):
    global MODEL_NAME_OR_PATH, MY_MODEL, MY_TOKENIZER
    # Initialize the Accelerator
    if accelerator is None:
        accelerator = Accelerator()

    # Load the translation model and tokenizer
    check_or_load_model(model_name_or_path,
                        quantization=None,
                        lora_weights_name_or_path=None,
                        dtype=None,
                        force_auto_device_map=False,
                        trust_remote_code=False,
                        accelerator=accelerator)

    if source_lang:
        MY_TOKENIZER.src_lang = source_lang

    if target_lang:
        lang_code_to_idx = MY_TOKENIZER.lang_code_to_id.get(target_lang, None)
        if lang_code_to_idx is None:
            raise ValueError(f"Target language {target_lang} not supported by the tokenizer.")
        gen_kwargs["forced_bos_token_id"] = lang_code_to_idx

    # Ensure the output directory exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Process each .docx file in the folder
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.docx'):
            file_path = os.path.join(folder_path, file_name)
            output_file_path = os.path.join(output_folder, f"{os.path.splitext(file_name)[0]}_translated.docx")
            translate_docx_file(file_path, output_file_path, gen_kwargs, accelerator)
            print(f"Translated {file_name} and saved to {output_file_path}")


def translate_2_zh(sentences_dir: Optional[str],
                   output_path: str,
                   source_lang: Optional[str],
                   target_lang: Optional[str],
                   model_name_or_path: str = "facebook/m2m100_1.2B",
                   straight_translate: bool = False,
                   switch_model_en_2_zh: bool = False,
                   accelerator: Accelerator = None,
                   gen_kwargs: dict = None):
    os.makedirs(TMP_FOLDER, exist_ok=True)
    # straight_translate = False
    if straight_translate:
        translate_folder(
            folder_path=sentences_dir,
            output_folder=output_path,
            source_lang=source_lang,
            target_lang=target_lang,
            model_name_or_path=model_name_or_path,
            accelerator=accelerator,
            gen_kwargs=gen_kwargs
        )
    else:
        # 翻译至英文
        translate_folder(
            folder_path=sentences_dir,
            output_folder=TMP_FOLDER,
            source_lang=source_lang,
            target_lang="eng_Latn",
            model_name_or_path=model_name_or_path,
            accelerator=accelerator,
            gen_kwargs=gen_kwargs
        )
        if switch_model_en_2_zh:
            model_name_or_path = ('./cache/models--facebook--nllb-200-distilled-600M/snapshots'
                                  '/f8d333a098d19b4fd9a8b18f94170487ad3f821d')
        # 英译中
        translate_folder(
            folder_path=TMP_FOLDER,
            output_folder=output_path,
            source_lang="eng_Latn",
            target_lang=target_lang,
            model_name_or_path=model_name_or_path,
            accelerator=accelerator,
            gen_kwargs=gen_kwargs
        )
        delete_folder_contents(TMP_FOLDER)


@update_task_status
def translate_with_task_id(task_id: str,
                           sentences_dir: Optional[str],
                           output_path: str,
                           source_lang: Optional[str],
                           target_lang: Optional[str],
                           model_name_or_path: str = "facebook/m2m100_1.2B",
                           straight_translate: bool = False,
                           switch_model_en_2_zh: bool = False,
                           accelerator: Accelerator = None,
                           gen_kwargs: dict = None):
    translate_2_zh(sentences_dir=sentences_dir,
                   output_path=output_path,
                   source_lang=source_lang,
                   target_lang=target_lang,
                   model_name_or_path=model_name_or_path,
                   straight_translate=straight_translate,
                   switch_model_en_2_zh=switch_model_en_2_zh,
                   gen_kwargs=gen_kwargs,
                   accelerator=accelerator)
