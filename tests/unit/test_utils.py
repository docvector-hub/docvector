"""Tests for utility functions."""

import pytest

from docvector.utils import (
    clean_text,
    compute_hash,
    compute_text_hash,
    count_tokens_approximate,
    normalize_whitespace,
    remove_html_tags,
    truncate_text,
)


class TestHashUtils:
    """Test hashing utilities."""

    def test_compute_hash_string(self):
        """Test computing hash from string."""
        result = compute_hash("test string")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex length

    def test_compute_hash_bytes(self):
        """Test computing hash from bytes."""
        result = compute_hash(b"test bytes")
        assert isinstance(result, str)
        assert len(result) == 64

    def test_compute_hash_consistency(self):
        """Test hash consistency."""
        hash1 = compute_hash("same content")
        hash2 = compute_hash("same content")
        assert hash1 == hash2

    def test_compute_hash_different(self):
        """Test different content produces different hash."""
        hash1 = compute_hash("content 1")
        hash2 = compute_hash("content 2")
        assert hash1 != hash2

    def test_compute_text_hash(self):
        """Test text hash wrapper."""
        result = compute_text_hash("test text")
        assert isinstance(result, str)
        assert len(result) == 64


class TestTextUtils:
    """Test text processing utilities."""

    def test_normalize_whitespace_multiple_spaces(self):
        """Test normalizing multiple spaces."""
        text = "hello    world"
        result = normalize_whitespace(text)
        assert result == "hello world"

    def test_normalize_whitespace_tabs(self):
        """Test normalizing tabs."""
        text = "hello\tworld"
        result = normalize_whitespace(text)
        assert result == "hello world"

    def test_normalize_whitespace_line_endings(self):
        """Test normalizing line endings."""
        text = "line1\r\nline2\rline3"
        result = normalize_whitespace(text)
        assert result == "line1\nline2\nline3"

    def test_normalize_whitespace_empty_lines(self):
        """Test removing empty lines at start and end."""
        text = "\n\nhello\n\n"
        result = normalize_whitespace(text)
        assert result == "hello"

    def test_remove_html_tags_basic(self):
        """Test removing basic HTML tags."""
        text = "<p>Hello <strong>world</strong></p>"
        result = remove_html_tags(text)
        assert result == "Hello world"

    def test_remove_html_tags_script(self):
        """Test removing script tags."""
        text = "<script>alert('hi')</script><p>Content</p>"
        result = remove_html_tags(text)
        assert "alert" not in result
        assert "Content" in result

    def test_remove_html_tags_style(self):
        """Test removing style tags."""
        text = "<style>body{}</style><p>Content</p>"
        result = remove_html_tags(text)
        assert "body{}" not in result
        assert "Content" in result

    def test_remove_html_tags_entities(self):
        """Test decoding HTML entities."""
        text = "&lt;div&gt; &amp; &quot;test&quot;"
        result = remove_html_tags(text)
        assert result == '<div> & "test"'

    def test_clean_text_basic(self):
        """Test basic text cleaning."""
        text = "<p>Hello   world</p>"
        result = clean_text(text)
        assert result == "Hello world"

    def test_clean_text_no_html_removal(self):
        """Test cleaning without HTML removal."""
        text = "<p>Hello   world</p>"
        result = clean_text(text, remove_html=False)
        assert "<p>" in result

    def test_truncate_text_short(self):
        """Test truncating short text (no truncation)."""
        text = "Short text"
        result = truncate_text(text, max_length=100)
        assert result == "Short text"

    def test_truncate_text_long(self):
        """Test truncating long text."""
        text = "This is a very long text that needs truncation"
        result = truncate_text(text, max_length=20)
        assert len(result) <= 20
        assert result.endswith("...")

    def test_truncate_text_preserve_words(self):
        """Test truncating at word boundary."""
        text = "Hello world this is a test"
        result = truncate_text(text, max_length=15, preserve_words=True)
        assert not result.startswith("Hello world t")  # Not mid-word
        assert result.endswith("...")

    def test_truncate_text_no_preserve_words(self):
        """Test truncating without preserving words."""
        text = "Hello world"
        result = truncate_text(text, max_length=8, preserve_words=False)
        assert result == "Hello..."

    def test_count_tokens_approximate(self):
        """Test approximate token counting."""
        text = "This is a test"  # ~4 tokens
        result = count_tokens_approximate(text)
        assert result > 0
        assert result < len(text)  # Should be less than character count

    def test_count_tokens_empty(self):
        """Test token counting with empty text."""
        result = count_tokens_approximate("")
        assert result == 0
