"""Text processing utilities for content extraction and normalization.

This module provides robust text extraction capabilities for handling various
data structures commonly encountered in LangChain applications, including
content blocks, messages, and mixed data types.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def _coerce_str(value: Any) -> str:
    """Safely convert any value to string, returning empty string on failure.
    
    Args:
        value (Any): Value to convert to string
        
    Returns:
        str: String representation of value, or empty string if conversion fails
    """
    try:
        return str(value)
    except Exception:
        return ""


def _extract_from_content_item(item: Any) -> str:
    """Extract text content from a single content item.
    
    Handles various item types including strings, dictionaries, and objects
    with text attributes.
    
    Args:
        item (Any): Content item to extract text from
        
    Returns:
        str: Extracted text content
    """
    # Direct string
    if isinstance(item, str):
        return item
    # Dict-like
    if isinstance(item, dict):
        return _extract_from_dict(item)
    # Objects with attributes or anything else
    return _extract_from_obj_with_attrs(item)


def _extract_from_dict(item: dict[str, Any]) -> str:
    """Extract text content from dictionary-like content structures.
    
    Searches for common text fields in dictionaries, including nested structures
    commonly found in LangChain content blocks.
    
    Args:
        item (dict[str, Any]): Dictionary to extract text from
        
    Returns:
        str: Extracted text content, or empty string if no text found
        
    Text Field Priority:
        1. Direct fields: text, content, input, message
        2. Nested fields: data, page_content
        3. Recursive extraction for nested structures
    """
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
    """Extract text content from objects with text attributes.
    
    Attempts to extract text from objects that have common text attributes
    like 'text' or 'content'.
    
    Args:
        item (Any): Object to extract text from
        
    Returns:
        str: Extracted text content, or string representation of the object
    """
    for attr in ("text", "content"):
        if hasattr(item, attr):
            try:
                return to_plain_text(getattr(item, attr))
            except Exception:
                continue
    return _coerce_str(item)


def to_plain_text(content: Any) -> str:
    """Convert various content structures to plain text.
    
    Provides robust text extraction from diverse data structures commonly
    encountered in LangChain applications, including content blocks, messages,
    and mixed data types.
    
    Args:
        content (Any): Content to convert to plain text. Can be:
            - str: Returned as-is
            - list/tuple: Items extracted and joined with newlines
            - dict: Text extracted from common text fields
            - object: Text extracted from .content or .text attributes
            - None: Returns empty string
            - other: Converted using str()
            
    Returns:
        str: Plain text representation of the content, stripped of extra whitespace
        
    Examples:
        >>> to_plain_text("Hello world")
        "Hello world"
        
        >>> to_plain_text([{"text": "Hello"}, {"text": "world"}])
        "Hello\nworld"
        
        >>> to_plain_text({"content": "Hello world"})
        "Hello world"
        
        >>> class ContentObj:
        ...     def __init__(self, text):
        ...         self.content = text
        >>> to_plain_text(ContentObj("Hello world"))
        "Hello world"
        
    Supported Structures:
        - LangChain content blocks with text/content fields
        - Message objects with content attributes
        - Nested dictionaries with page_content or data fields
        - Mixed iterables of text and content objects
        - Any object with .content or .text attributes
        
    Note:
        This function is designed to be resilient and will attempt multiple
        extraction strategies before falling back to string conversion.
        Non-text content (like images) in structured data is safely ignored.
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
