# import ctranslate2
# import transformers
#
# src_lang = "khk_Cyrl"
# tgt_lang = "zho_Hans"
#
# translator = ctranslate2.Translator("./cache/ct2/facebook-nllb-200-distilled-600M", intra_threads=4)
# tokenizer = transformers.AutoTokenizer.from_pretrained("./cache/models--facebook--nllb-200-distilled-600M/snapshots"
#                                                        "/f8d333a098d19b4fd9a8b18f94170487ad3f821d", src_lang=src_lang)
#
# source = tokenizer.convert_ids_to_tokens(tokenizer.encode("Украинчууд оросын түрэмгийллийн эсрэг 790 хоног "
#                                                           "баатарлагаар тулалдаж эх орноо батлан хамгаалсаар байна. "
#                                                           "Хамгийн сүүлийн үеийн мэдээгээр Украины арми Донецк мужийн "
#                                                           "газар нутаг дээрхи хяналтаа алдсаарбайна. Оросын арми "
#                                                           "Авдеевкад Очеретино тосгоныг эзэлж, Часов Яр хот руу "
#                                                           "довтолгоогоо эрчимжүүлж байна. Эдүгээ Украин зөвхөн АНУ-ын "
#                                                           "цэргийн тусламжинд л найдаж байна."))
# target_prefix = [tgt_lang]
# results = translator.translate_batch([source,source,source,source], target_prefix=[target_prefix,target_prefix,target_prefix,target_prefix])
# target = results[0].hypotheses[0][1:]
#
# print(tokenizer.decode(tokenizer.convert_tokens_to_ids(target)))

# Load model directly
from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("hfl/chinese-llama-2-1.3b", cache_dir="./cache")
model = AutoModelForCausalLM.from_pretrained("hfl/chinese-llama-2-1.3b", cache_dir="./cache")