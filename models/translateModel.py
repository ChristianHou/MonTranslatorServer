# models.py
import ctranslate2
import transformers
from docx import Document
from tqdm import tqdm
from configparser import ConfigParser
import pandas as pd
import threading
from openpyxl import load_workbook

cfg = ConfigParser()
cfg.read('./config/config.ini')


class TranslatorSingleton:
    _cpu_instances = []
    _cuda_instances = []
    _tokenizers = {}
    _lock = threading.Lock()

    @classmethod
    def initialize_models(cls, num_cpu_models=2, num_cuda_models=2):
        for _ in range(num_cpu_models):
            cls._cpu_instances.append({
                "translator": ctranslate2.Translator(cfg["MODEL_LIST"][cfg["DEFAULT"]["SEQ_TRANSLATE_MODEL"]],
                                                     intra_threads=4),
                "task_count": threading.Semaphore(10)
            })
        for _ in range(num_cuda_models):
            cls._cuda_instances.append({
                "translator": ctranslate2.Translator(cfg["MODEL_LIST"][cfg["DEFAULT"]["FILE_TRANSLATE_MODEL"]],
                                                     device='cuda'),
                "task_count": threading.Semaphore(10)
            })

    @classmethod
    def _load_tokenizer(cls, src_lang: str):
        if (src_lang, "tokenizer") not in cls._tokenizers:
            cls._tokenizers[(src_lang, "tokenizer")] = transformers.AutoTokenizer.from_pretrained(
                cfg["TOKENIZER_LIST"][cfg["DEFAULT"]["SEQ_TRANSLATE_MODEL"]],
                src_lang=src_lang
            )
        return cls._tokenizers[(src_lang, "tokenizer")]

    @classmethod
    def _get_least_loaded_model(cls, use_cuda=False):
        instances = cls._cuda_instances if use_cuda else cls._cpu_instances
        least_loaded_instance = min(instances, key=lambda x: x["task_count"]._value)
        least_loaded_instance["task_count"].acquire()
        return least_loaded_instance

    @classmethod
    def _release_model(cls, model_instance, use_cuda=False):
        model_instance["task_count"].release()

    @classmethod
    def translate_sentence(cls, text: str, src_lang: str, tgt_lang: str, use_cuda=False) -> str:
        model_instance = cls._get_least_loaded_model(use_cuda)
        try:
            translator = model_instance["translator"]
            tokenizer = cls._load_tokenizer(src_lang)

            source = tokenizer.convert_ids_to_tokens(tokenizer.encode(text))
            target_prefix = [tgt_lang]
            results = translator.translate_batch([source], target_prefix=[target_prefix])
            target = results[0].hypotheses[0][1:]

            return tokenizer.decode(tokenizer.convert_tokens_to_ids(target))
        finally:
            cls._release_model(model_instance)

    @classmethod
    def translate_batch(cls, texts: list, src_lang: str, tgt_lang: str, use_cuda=False) -> list:
        model_instance = cls._get_least_loaded_model(use_cuda)
        try:
            translator = model_instance["translator"]
            tokenizer = cls._load_tokenizer(src_lang)

            sources = [tokenizer.convert_ids_to_tokens(tokenizer.encode(text)) for text in texts]
            target_prefix = [tgt_lang] * len(texts)
            results = translator.translate_batch(sources, target_prefix=[target_prefix])

            translations = [tokenizer.decode(tokenizer.convert_tokens_to_ids(result.hypotheses[0][1:])) for result in
                            results]
            return translations
        finally:
            cls._release_model(model_instance)


class DocxTranslator(TranslatorSingleton):
    @staticmethod
    def translate_run(run, src_lang, tgt_lang):
        if not run.text.strip():
            return ""

        translated_text = TranslatorSingleton.translate_sentence(run.text, src_lang, tgt_lang, use_cuda=True)
        return translated_text

    @staticmethod
    def translate_paragraph(paragraph, src_lang, tgt_lang):
        translated_runs = []

        for run in paragraph.runs:
            translated_text = DocxTranslator.translate_run(run, src_lang, tgt_lang)
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

    @staticmethod
    def translate_docx(input_path: str, output_path: str, src_lang: str, tgt_lang: str):
        doc = Document(input_path)
        translated_doc = Document()

        for para in tqdm(doc.paragraphs, desc=f"Translating {input_path}"):
            if para.text.strip():
                DocxTranslator.translate_paragraph(para, src_lang, tgt_lang)
                translated_doc.add_paragraph(para.text)

        translated_doc.save(output_path)


class TableTranslator(TranslatorSingleton):
    @staticmethod
    def translate_text(text, src_lang, tgt_lang):
        if text is None:
            return text
        lines = text.split('\n')
        translated_lines = [TranslatorSingleton.translate_sentence(line, src_lang, tgt_lang, use_cuda=True) for line in
                            lines]
        return '\n'.join(translated_lines)

    @staticmethod
    def translate_excel(input_path: str, output_path: str, src_lang: str, tgt_lang: str):
        wb = load_workbook(input_path)

        for sheet in wb.worksheets:
            # Dictionary to store merged cell ranges and their translated content
            translated_cells = {}
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value and isinstance(cell.value, str):
                        # Translate the text only if this cell is the first in a merged range or not merged
                        if cell.coordinate not in translated_cells:
                            translated_text = TableTranslator.translate_text(cell.value, src_lang, tgt_lang)
                            translated_cells[cell.coordinate] = translated_text

                            # Apply the translation to all cells in the merged range, if any
                            for merged_range in sheet.merged_cells.ranges:
                                if cell.coordinate in merged_range:
                                    for row in sheet[merged_range.coord]:
                                        for merged_cell in row:
                                            translated_cells[merged_cell.coordinate] = translated_text

            # Apply translated values back to the worksheet
            for coord, translated_text in translated_cells.items():
                sheet[coord].value = translated_text

            # Reapply the merged cells after translation
            for merged_cell in sheet.merged_cells.ranges:
                sheet.merge_cells(str(merged_cell))

        wb.save(output_path)

    @staticmethod
    def translate_csv(input_path: str, output_path: str, src_lang: str, tgt_lang: str):
        df = pd.read_csv(input_path)
        translated_df = df.applymap(
            lambda x: TableTranslator.translate_text(x, src_lang, tgt_lang) if isinstance(x, str) else x)
        translated_df.to_csv(output_path, index=False)
