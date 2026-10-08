from pathlib import Path

import sentencepiece as spm


# токенизатор XLM-R (его использует multilingual-e5): SentencePiece + схема идентификаторов fairseq.
# выдаёт те же id, что и tokenizer.json из HF (проверено на всех 1919 фразах проекта),
# но занимает в памяти ~20 МБ вместо ~280 МБ – иначе сервис не помещается в 512 МБ Render
class XlmrTokenizer:
    BOS, PAD, EOS, UNK = 0, 1, 2, 3  # служебные токены fairseq
    OFFSET = 1  # id SentencePiece сдвинуты на 1: в словаре fairseq впереди стоит <pad>

    def __init__(self, model_path: Path, max_length: int):
        self.sp = spm.SentencePieceProcessor(model_file=str(model_path))
        self.max_length = max_length

    def encode(self, text: str) -> list[int]:
        # id 0 у SentencePiece – неизвестный символ, у fairseq ему соответствует <unk> = 3
        pieces = [p + self.OFFSET if p else self.UNK for p in self.sp.encode(text, out_type=int)]
        return [self.BOS, *pieces[: self.max_length - 2], self.EOS]
