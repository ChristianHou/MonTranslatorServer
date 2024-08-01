from pydantic import BaseModel


class SourceRequest(BaseModel):
    client_ip:str
    sentences: str | None = None
    source_lang: str = None
    target_lang: str = None


class ResponseModel(BaseModel):
    result: str
