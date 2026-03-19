"""Prompt sanitization utilities."""

from __future__ import annotations

import re


def sanitize_prompt_text(text: str) -> str:
    """Strip control patterns that could be interpreted as LLM directives."""
    text = re.sub(r'\n{3,}', '\n\n', text)  # collapse visual separation attacks
    text = re.sub(
        r'</?(?:system|instruction|prompt|role|assistant|user)\b[^>]*>',
        '', text, flags=re.IGNORECASE,
    )
    return text.strip()
