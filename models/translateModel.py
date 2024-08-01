# models.py
import ctranslate2
import transformers
from docx import Document
from tqdm import tqdm
from configparser import ConfigParser
import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

cfg = ConfigParser()
cfg.read('./config/config.ini')


class TranslatorSingleton:
    _cpu_instance = None
    _cuda_instance = None
    _tokenizers = {}

    @classmethod
    def get_cpu_model(cls):
        if cls._cpu_instance is None:
            cls._cpu_instance = {
                "translator": ctranslate2.Translator(cfg["MODEL_LIST"][cfg["DEFAULT"]["SEQ_TRANSLATE_MODEL"]],
                                                     intra_threads=4)
            }
        return cls._cpu_instance

    @classmethod
    def get_cuda_model(cls):
        if cls._cuda_instance is None:
            cls._cuda_instance = {
                "translator": ctranslate2.Translator(cfg["MODEL_LIST"][cfg["DEFAULT"]["FILE_TRANSLATE_MODEL"]],
                                                     device='cuda')
            }
        return cls._cuda_instance

    @classmethod
    def _load_tokenizer(cls, src_lang: str):
        if src_lang not in cls._tokenizers:
            cls._tokenizers[src_lang] = transformers.AutoTokenizer.from_pretrained(
                cfg["TOKENIZER_LIST"][cfg["DEFAULT"]["SEQ_TRANSLATE_MODEL"]],
                src_lang=src_lang
            )
        return cls._tokenizers[src_lang]

    @classmethod
    def translate_sentence(cls, text: str, src_lang: str, tgt_lang: str) -> str:
        model = cls.get_cpu_model()
        translator = model["translator"]
        tokenizer = cls._load_tokenizer(src_lang)

        source = tokenizer.convert_ids_to_tokens(tokenizer.encode(text))
        target_prefix = [tgt_lang]
        results = translator.translate_batch([source], target_prefix=[target_prefix])
        target = results[0].hypotheses[0][1:]

        return tokenizer.decode(tokenizer.convert_tokens_to_ids(target))

    @classmethod
    def translate_sentence_with_cuda(cls, text: str, src_lang: str, tgt_lang: str) -> str:
        model = cls.get_cuda_model()
        translator = model["translator"]
        tokenizer = cls._load_tokenizer(src_lang)

        source = tokenizer.convert_ids_to_tokens(tokenizer.encode(text))
        target_prefix = [tgt_lang]
        results = translator.translate_batch([source], target_prefix=[target_prefix])
        target = results[0].hypotheses[0][1:]

        return tokenizer.decode(tokenizer.convert_tokens_to_ids(target))

    @classmethod
    def translate_batch(cls, texts: list, src_lang: str, tgt_lang: str) -> list:
        model = cls.get_cpu_model()
        translator = model["translator"]
        tokenizer = cls._load_tokenizer(src_lang)

        sources = [tokenizer.convert_ids_to_tokens(tokenizer.encode(text)) for text in texts]
        target_prefix = [tgt_lang] * len(texts)
        results = translator.translate_batch(sources, target_prefix=[target_prefix])

        translations = [tokenizer.decode(tokenizer.convert_tokens_to_ids(result.hypotheses[0][1:])) for result in
                        results]
        return translations

    @classmethod
    def translate_batch_with_cuda(cls, texts: list, src_lang: str, tgt_lang: str) -> list:
        model = cls.get_cuda_model()
        translator = model["translator"]
        tokenizer = cls._load_tokenizer(src_lang)

        sources = [tokenizer.convert_ids_to_tokens(tokenizer.encode(text)) for text in texts]
        target_prefix = [tgt_lang] * len(texts)
        results = translator.translate_batch(sources, target_prefix=[target_prefix])

        translations = [tokenizer.decode(tokenizer.convert_tokens_to_ids(result.hypotheses[0][1:])) for result in
                        results]
        return translations

    @classmethod
    def translate_sentences_via_intermediate(cls, text: str, src_lang: str, tgt_lang: str) -> str:
        intermediate_lang = "eng_Latn"
        # 从 src_lang 翻译到中间语言
        intermediate_text = cls.translate_sentence(text, src_lang, intermediate_lang)
        # 从中间语言翻译到 tgt_lang
        final_text = cls.translate_sentence(intermediate_text, intermediate_lang, tgt_lang)
        return final_text

    @classmethod
    def translate_batch_via_intermediate(cls, texts: list, src_lang: str, tgt_lang: str) -> list:
        intermediate_lang = "eng_Latn"
        # 从 src_lang 翻译到中间语言
        intermediate_texts = cls.translate_batch(texts, src_lang, intermediate_lang)
        # 从中间语言翻译到 tgt_lang
        final_texts = cls.translate_batch(intermediate_texts, intermediate_lang, tgt_lang)
        return final_texts

    @classmethod
    def translate_batch_with_cuda_via_intermediate(cls, texts: list, src_lang: str, tgt_lang: str) -> list:
        intermediate_lang = "eng_Latn"
        # 从 src_lang 翻译到中间语言
        intermediate_texts = cls.translate_batch_with_cuda(texts, src_lang, intermediate_lang)
        # 从中间语言翻译到 tgt_lang
        final_texts = cls.translate_batch_with_cuda(intermediate_texts, intermediate_lang, tgt_lang)
        return final_texts


class DocxTranslator(TranslatorSingleton):
    @staticmethod
    def translate_run(run, src_lang, tgt_lang):
        if not run.text.strip():
            return ""

        translated_text = TranslatorSingleton.translate_sentence_with_cuda(run.text, src_lang, tgt_lang)
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
        translated_lines = [TranslatorSingleton.translate_sentence_with_cuda(line, src_lang, tgt_lang) for line in
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
        translated_df = df.applymap(lambda x: TableTranslator.translate_text(x, src_lang, tgt_lang) if isinstance(x, str) else x)
        translated_df.to_csv(output_path, index=False)