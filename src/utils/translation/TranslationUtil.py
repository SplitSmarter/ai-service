import enum
from contextvars import ContextVar
from typing import Callable

_lang_ctx: ContextVar[Callable[[str], str]] = ContextVar("language_context", default=lambda x: x)


def _(text, **kwargs) -> str:
    if hasattr(text, 'value'):
        text = text.value

    try:
        translated_text = _lang_ctx.get()(str(text))

        if kwargs:
            return translated_text.format(**kwargs)
        return translated_text
    except (LookupError, KeyError, IndexError):
        return str(text)