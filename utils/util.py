import os
from transformers import (
    AutoConfig,
    AutoTokenizer,
    AutoModelForCausalLM,
    AutoModelForSeq2SeqLM,
    BitsAndBytesConfig,
    PreTrainedModel,
    PreTrainedTokenizerBase,
)
from transformers.models.auto.modeling_auto import (
    MODEL_FOR_CAUSAL_LM_MAPPING_NAMES,
    MODEL_FOR_SEQ_TO_SEQ_CAUSAL_LM_MAPPING_NAMES,
)
import ctranslate2 as ct2
from typing import Optional, Tuple
import torch
import json


# 加载模型
def load_model_for_inference(
        weights_path: str,
        quantization: Optional[int] = None,
        lora_weights_name_or_path: Optional[str] = None,
        torch_dtype: Optional[str] = None,
        force_auto_device_map: bool = False,
        trust_remote_code: bool = False,
) -> Tuple[PreTrainedModel, PreTrainedTokenizerBase]:
    """
    Load any Decoder model for inference.

    Args:
        weights_path (`str`):
            The path to your local model weights and tokenizer. You can also provide a
            huggingface hub model name.
        quantization (`int`, optional):
            '4' or '8' for 4 bits or 8 bits quantization or None for 16/32bits training. Defaults to `None`.

            Requires bitsandbytes library: https://github.com/TimDettmers/bitsandbytes
        lora_weights_name_or_path (`Optional[str]`, optional):
            If the model has been trained with LoRA, path or huggingface hub name to the
            pretrained weights. Defaults to `None`.
        torch_dtype (`Optional[str]`, optional):
            The torch dtype to use for the model. If set to `"auto"`, the dtype will be
            automatically derived. Defaults to `None`. If quantization is enabled, we will override
            this to 'torch.bfloat16'.
        force_auto_device_map (`bool`, optional):
            Whether to force the use of the auto device map. If set to True, the model will be split across
            GPUs and CPU to fit the model in memory. If set to False, a full copy of the model will be loaded
            into each GPU. Defaults to False.
        trust_remote_code (`bool`, optional):
            Trust the remote code from HuggingFace model hub. Defaults to False.

    Returns:
        `Tuple[PreTrainedModel, PreTrainedTokenizerBase]`:
            The loaded model and tokenizer.
    """

    if type(quantization) == str:
        quantization = int(quantization)
    assert (quantization is None) or (
            quantization in [4, 8]
    ), f"Quantization must be 4 or 8, or None for FP32/FP16 training. You passed: {quantization}"

    print(f"Loading model from {weights_path}")

    config = AutoConfig.from_pretrained(
        weights_path, trust_remote_code=trust_remote_code, cache_dir='./cache/'
    )

    torch_dtype = (
        torch_dtype if torch_dtype in ["auto", None] else getattr(torch, torch_dtype)
    )

    tokenizer: PreTrainedTokenizerBase = AutoTokenizer.from_pretrained(
        weights_path, add_eos_token=True, trust_remote_code=trust_remote_code, cache_dir='./cache/'
    )

    if tokenizer.pad_token_id is None:
        if "<|padding|>" in tokenizer.get_vocab():
            # StabilityLM specific fix
            tokenizer.add_special_tokens({"pad_token": "<|padding|>"})
        elif tokenizer.unk_token is not None:
            print(
                "Tokenizer does not have a pad token, we will use the unk token as pad token."
            )
            tokenizer.pad_token_id = tokenizer.unk_token_id
        else:
            print(
                "Tokenizer does not have a pad token. We will use the eos token as pad token."
            )
            tokenizer.pad_token_id = tokenizer.eos_token_id

    quant_args = {}

    if quantization is not None:
        quant_args = (
            {"load_in_4bit": True} if quantization == 4 else {"load_in_8bit": True}
        )
        if quantization == 4:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16
                if torch_dtype in ["auto", None]
                else torch_dtype,
            )

        else:
            bnb_config = BitsAndBytesConfig(
                load_in_8bit=True,
            )
        print(
            f"Bits and Bytes config: {json.dumps(bnb_config.to_dict(), indent=4, ensure_ascii=False)}"
        )
    else:
        print(f"Loading model with dtype: {torch_dtype}")
        bnb_config = None

    if config.model_type in MODEL_FOR_SEQ_TO_SEQ_CAUSAL_LM_MAPPING_NAMES:
        print(
            f"Model {weights_path} is a encoder-decoder model. We will load it as a Seq2SeqLM model."
        )
        model: PreTrainedModel = AutoModelForSeq2SeqLM.from_pretrained(
            pretrained_model_name_or_path=weights_path,
            device_map="auto" if force_auto_device_map else None,
            torch_dtype=torch_dtype,
            quantization_config=bnb_config,
            trust_remote_code=trust_remote_code,
            cache_dir='./cache/',
            **quant_args,
        )

    elif config.model_type in MODEL_FOR_CAUSAL_LM_MAPPING_NAMES:
        print(
            f"Model {weights_path} is an encoder-only model. We will load it as a CausalLM model."
        )
        model: PreTrainedModel = AutoModelForCausalLM.from_pretrained(
            pretrained_model_name_or_path=weights_path,
            device_map="auto" if force_auto_device_map else None,
            torch_dtype=torch_dtype,
            trust_remote_code=trust_remote_code,
            quantization_config=bnb_config,
            cache_dir='./cache/',
            **quant_args,
        )

        # Ensure that the padding token is added to the left of the input sequence.
        tokenizer.padding_side = "left"
    else:
        raise ValueError(
            f"Model {weights_path} of type {config.model_type} is not supported by EasyTranslate."
            "Supported models are:\n"
            f"Seq2SeqLM: {MODEL_FOR_SEQ_TO_SEQ_CAUSAL_LM_MAPPING_NAMES}\n"
            f"CausalLM: {MODEL_FOR_CAUSAL_LM_MAPPING_NAMES}\n"
        )

    if lora_weights_name_or_path:
        from peft import PeftModel

        print(f"Loading pretrained LORA weights from {lora_weights_name_or_path}")
        model = PeftModel.from_pretrained(model, lora_weights_name_or_path)

        if quantization is None:
            # If we are not using quantization, we merge the LoRA layers into the model for faster inference.
            # This is not possible if we are using 4/8 bit quantization.
            model = model.merge_and_unload()

    return model, tokenizer


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
    os.removedirs(folder_path)
