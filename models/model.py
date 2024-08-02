from pydantic import BaseModel


class SourceRequest(BaseModel):
    client_ip: str | None = None
    sentences: str | None = None
    source_lang: str = None
    target_lang: str = None
    via_eng: bool = False


class ResponseModel(BaseModel):
    result: str
