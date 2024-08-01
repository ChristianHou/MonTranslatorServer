# file_handler.py
import os
from io import BytesIO
from docx import Document
from typing import List
from fastapi import UploadFile, HTTPException
import pandas as pd


class FileHandler:
    @classmethod
    def _save_docx(cls, file: UploadFile, directory: str) -> None:
        try:
            file_stream = BytesIO(file.file.read())
            document = Document(file_stream)
            new_file_location = os.path.join(directory, file.filename)
            document.save(new_file_location)
        finally:
            file_stream.close()


    @classmethod
    def _save_excel(cls, file: UploadFile, directory: str) -> None:
        try:
            file_stream = BytesIO(file.file.read())
            df = pd.read_excel(file_stream)
            new_file_location = os.path.join(directory, file.filename)
            df.to_excel(new_file_location, index=False)
        except Exception as e:
            raise e
        finally:
            file_stream.close()


    @classmethod
    def _save_csv(cls, file: UploadFile, directory: str) -> None:
        try:
            file_stream = BytesIO(file.file.read())
            df = pd.read_csv(file_stream)
            new_file_location = os.path.join(directory, file.filename)
            df.to_csv(new_file_location, index=False)
        finally:
            file_stream.close()

    @classmethod
    def process_files(cls, upload_directory: str, files: List[UploadFile]) -> None:
        os.makedirs(upload_directory, exist_ok=True)

        for file in files:
            if not file.filename.endswith(('.docx', '.xlsx', '.xls', '.csv')):
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")

            try:
                if file.filename.endswith('.docx'):
                    cls._save_docx(file, upload_directory)
                elif file.filename.endswith(('.xlsx', '.xls')):
                    cls._save_excel(file, upload_directory)
                elif file.filename.endswith('.csv'):
                    cls._save_csv(file, upload_directory)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error processing file {file.filename}: {str(e)}")
