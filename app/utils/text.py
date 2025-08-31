from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def _coerce_str(value: Any) -> str:
    try:
        return str(value)
    except Exception:
        return ""


def _extract_from_content_item(item: Any) -> str:
    # Direct string
    if isinstance(item, str):
        return item
    # Dict-like
    if isinstance(item, dict):
        return _extract_from_dict(item)
    # Objects with attributes or anything else
    return _extract_from_obj_with_attrs(item)


def _extract_from_dict(item: dict[str, Any]) -> str:
    # Prefer explicit text fields
    for key in ("text", "content", "input", "message"):
        value = item.get(key)
        if isinstance(value, str | int | float):
            return _coerce_str(value)
    # Sometimes the text is nested
    nested = item.get("data") or item.get("page_content")
    if isinstance(nested, str | int | float):
        return _coerce_str(nested)
    if isinstance(nested, dict | list):
        return to_plain_text(nested)
    # Otherwise fall back to empty for non-text blocks (images, etc.)
    return ""


def _extract_from_obj_with_attrs(item: Any) -> str:
    for attr in ("text", "content"):
        if hasattr(item, attr):
            try:
                return to_plain_text(getattr(item, attr))
            except Exception:
                continue
    return _coerce_str(item)


def to_plain_text(content: Any) -> str:
    """Best-effort conversion of various content structures to a plain string.

    Handles:
    - str: returned as-is
    - list/tuple of mixed items/dicts (LangChain content blocks): concatenated with newlines
    - dicts with common text keys: extracts the text
    - objects exposing .content / .text: extracts recursively
    - anything else: coerced to str()
    """
    if content is None:
        return ""

    # Already a string
    if isinstance(content, str):
        return content

    # Iterable of content blocks
    if isinstance(content, Iterable) and not isinstance(content, bytes | bytearray | dict):
        parts: list[str] = []
        for it in content:
            part = _extract_from_content_item(it)
            if part:
                parts.append(part)
        return "\n".join(parts).strip()

    # Dict-like content
    if isinstance(content, dict):
        return _extract_from_content_item(content).strip()

    # Objects with content/text attributes
    for attr in ("content", "text"):
        if hasattr(content, attr):
            try:
                return to_plain_text(getattr(content, attr)).strip()
            except Exception:
                pass

    # Fallback
    return _coerce_str(content).strip()


__all__ = ["to_plain_text"]
