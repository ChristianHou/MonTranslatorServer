from pydantic import BaseModel


class SourceRequest(BaseModel):
    sentences: str | None = None
    sentences_path: str = None
    sentences_dir: str = None
    output_path: str = './sample_text/result.txt'
    files_extension: str = "txt"
    source_lang: str = None
    target_lang: str = None
    starting_batch_size: int = 4
    model_name_or_path: str = None
    lora_weights_name_or_path: str = None
    max_length: int = 1024
    num_beams: int = 5
    precision: str = None
    do_sample: bool = False
    temperature: float = 0.8
    top_k: int = 100
    top_p: float = 0.75
    repetition_penalty: float = 1.0
    keep_special_tokens: bool = False
    keep_tokenization_spaces: bool = False
    num_return_sequences: int = 1
    force_auto_device_map: bool = False
    prompt: str = None
    trust_remote_code: bool = False


class ResponseModel(BaseModel):
    result: str
