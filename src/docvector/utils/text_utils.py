"""Text processing utilities."""

import re
from typing import Optional


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.

    - Replace multiple spaces with single space
    - Replace tabs with spaces
    - Remove leading/trailing whitespace
    - Normalize line endings

    Args:
        text: Input text

    Returns:
        Normalized text
    """
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Replace tabs with spaces
    text = text.replace("\t", " ")

    # Replace multiple spaces with single space
    text = re.sub(r" +", " ", text)

    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split("\n")]

    # Remove empty lines at start and end
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()

    return "\n".join(lines)


def remove_html_tags(text: str) -> str:
    """
    Remove HTML tags from text.

    Args:
        text: Text with HTML tags

    Returns:
        Text without HTML tags
    """
    # Remove script and style elements
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Remove HTML comments
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Decode common HTML entities
    entities = {
        "&nbsp;": " ",
        "&lt;": "<",
        "&gt;": ">",
        "&amp;": "&",
        "&quot;": '"',
        "&apos;": "'",
    }
    for entity, char in entities.items():
        text = text.replace(entity, char)

    return text


def clean_text(text: str, remove_html: bool = True) -> str:
    """
    Clean and normalize text.

    - Remove HTML tags (optional)
    - Normalize whitespace
    - Remove control characters

    Args:
        text: Input text
        remove_html: Whether to remove HTML tags

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove HTML tags if requested
    if remove_html:
        text = remove_html_tags(text)

    # Remove control characters (except newline and tab)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Normalize whitespace
    text = normalize_whitespace(text)

    return text


def truncate_text(
    text: str,
    max_length: int,
    suffix: str = "...",
    preserve_words: bool = True,
) -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Input text
        max_length: Maximum length (including suffix)
        suffix: Suffix to append if truncated
        preserve_words: If True, truncate at word boundary

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    # Account for suffix length
    truncate_length = max_length - len(suffix)

    if preserve_words:
        # Find last space before truncate point
        last_space = text.rfind(" ", 0, truncate_length)
        if last_space > 0:
            truncate_length = last_space

    return text[:truncate_length] + suffix


def count_tokens_approximate(text: str) -> int:
    """
    Approximate token count for text.

    Uses simple heuristic: ~4 characters per token.
    For more accurate counting, use tiktoken or similar.

    Args:
        text: Input text

    Returns:
        Approximate token count
    """
    # Simple approximation: ~4 characters per token
    # This is roughly accurate for English text
    return len(text) // 4


def extract_title_from_text(text: str, max_length: int = 100) -> Optional[str]:
    """
    Extract a title from text (first line or paragraph).

    Args:
        text: Input text
        max_length: Maximum title length

    Returns:
        Extracted title or None
    """
    if not text:
        return None

    # Try to get first non-empty line
    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        if line:
            return truncate_text(line, max_length, suffix="...")

    return None
