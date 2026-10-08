import re
from dataclasses import dataclass

# реплика-уточнение начинается с союза: «а в магистратуре?», «ал магистратурада?», «and for a master's?»
FOLLOW_UP_RE = re.compile(r"^\W*(а|и|ал|және|сонда|тогда|and|also|what about|how about)\b", re.IGNORECASE)
MAX_FOLLOW_UP_WORDS = 5  # уточнение короткое; длинная реплика с союзом – обычно самостоятельный вопрос


@dataclass
class Context:
    text: str    # предыдущий вопрос (вместе с его собственным контекстом, если он был)
    intent: str  # тема предыдущего ответа


def is_follow_up(text: str) -> bool:
    return bool(FOLLOW_UP_RE.match(text))


# контекст диалога: уточнение классифицируется вместе с предыдущим вопросом («Сколько стоит ВТиПО? а в магистратуре?»).
# наивное правило «всегда склеивать» ломает вопросы не по теме: «Какой курс евро?» прилипал к прошлой теме.
# поэтому склеенный вариант принимается, только если реплика – уточнение (союз в начале) и
#  - без контекста она не понята, или
#  - она короткая, а склеенный вариант остаётся в той же группе тем, что и предыдущий ответ
def use_context(text: str, alone_recognized: bool, joint_recognized: bool, same_group: bool) -> bool:
    if not is_follow_up(text) or not joint_recognized:
        return False
    return not alone_recognized or (same_group and len(text.split()) <= MAX_FOLLOW_UP_WORDS)
