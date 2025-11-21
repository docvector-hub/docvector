"""Code snippet extraction and quality scoring."""

import re
from dataclasses import dataclass
from typing import List, Optional

from bs4 import BeautifulSoup


@dataclass
class CodeSnippet:
    """Represents an extracted code snippet."""

    content: str
    language: Optional[str] = None
    quality_score: float = 0.0
    formatting_score: float = 0.0
    metadata_score: float = 0.0
    initialization_score: float = 0.0
    context: Optional[str] = None  # Surrounding text for context
    start_char: Optional[int] = None
    end_char: Optional[int] = None


class CodeExtractor:
    """Extracts code snippets from HTML and markdown content."""

    # Language identifiers commonly used in code blocks
    LANGUAGE_PATTERNS = [
        "python",
        "javascript",
        "typescript",
        "java",
        "csharp",
        "cpp",
        "c",
        "go",
        "rust",
        "ruby",
        "php",
        "swift",
        "kotlin",
        "scala",
        "shell",
        "bash",
        "sql",
        "html",
        "css",
        "json",
        "yaml",
        "xml",
        "markdown",
    ]

    def __init__(self):
        """Initialize the code extractor."""
        pass

    def extract_from_html(self, html_content: str) -> List[CodeSnippet]:
        """
        Extract code snippets from HTML content.

        Args:
            html_content: HTML content to extract from

        Returns:
            List of CodeSnippet objects
        """
        soup = BeautifulSoup(html_content, "html.parser")
        snippets = []

        # Extract from <code> blocks
        for code_tag in soup.find_all("code"):
            # Check if it's inside a <pre> tag (block code)
            parent = code_tag.parent
            if parent and parent.name == "pre":
                content = code_tag.get_text()
                if len(content.strip()) < 10:  # Skip very short snippets
                    continue

                # Try to detect language from class attribute
                language = self._detect_language_from_classes(code_tag.get("class", []))

                # Get surrounding context
                context = self._extract_context(code_tag)

                snippet = CodeSnippet(
                    content=content,
                    language=language,
                    context=context,
                )

                # Score the snippet
                self._score_snippet(snippet)

                snippets.append(snippet)

        # Extract from <script> tags (for embedded code examples)
        for script_tag in soup.find_all("script", {"type": "text/plain"}):
            content = script_tag.get_text()
            if len(content.strip()) < 10:
                continue

            language = self._detect_language_from_classes(script_tag.get("class", []))
            context = self._extract_context(script_tag)

            snippet = CodeSnippet(
                content=content,
                language=language,
                context=context,
            )
            self._score_snippet(snippet)
            snippets.append(snippet)

        return snippets

    def extract_from_markdown(self, markdown_content: str) -> List[CodeSnippet]:
        """
        Extract code snippets from Markdown content.

        Args:
            markdown_content: Markdown content to extract from

        Returns:
            List of CodeSnippet objects
        """
        snippets = []

        # Pattern for fenced code blocks with optional language
        pattern = r"```(\w+)?\n(.*?)```"

        for match in re.finditer(pattern, markdown_content, re.DOTALL):
            language = match.group(1)
            content = match.group(2).strip()

            if len(content) < 10:  # Skip very short snippets
                continue

            # Get context (text before the code block)
            start_pos = match.start()
            context_start = max(0, start_pos - 200)
            context = markdown_content[context_start:start_pos].strip()

            snippet = CodeSnippet(
                content=content,
                language=language,
                context=context,
                start_char=match.start(),
                end_char=match.end(),
            )

            self._score_snippet(snippet)
            snippets.append(snippet)

        # Pattern for indented code blocks (4 spaces or 1 tab)
        indented_pattern = r"(?:^|\n)((?:(?:    |\t).+\n?)+)"

        for match in re.finditer(indented_pattern, markdown_content, re.MULTILINE):
            content = match.group(1)
            # Remove indentation
            content = re.sub(r"^(?:    |\t)", "", content, flags=re.MULTILINE)
            content = content.strip()

            if len(content) < 10:
                continue

            # Get context
            start_pos = match.start()
            context_start = max(0, start_pos - 200)
            context = markdown_content[context_start:start_pos].strip()

            snippet = CodeSnippet(
                content=content,
                language=None,  # Can't detect language from indented blocks
                context=context,
                start_char=match.start(),
                end_char=match.end(),
            )

            self._score_snippet(snippet)
            snippets.append(snippet)

        return snippets

    def _detect_language_from_classes(self, classes: List[str]) -> Optional[str]:
        """
        Detect programming language from CSS classes.

        Args:
            classes: List of CSS class names

        Returns:
            Detected language or None
        """
        if not classes:
            return None

        for cls in classes:
            cls_lower = str(cls).lower()

            # Common patterns: "language-python", "lang-python", "python"
            for lang in self.LANGUAGE_PATTERNS:
                if lang in cls_lower:
                    return lang

            # Highlight.js style
            if cls_lower.startswith("hljs-"):
                return cls_lower.replace("hljs-", "")

        return None

    def _extract_context(self, tag) -> Optional[str]:
        """
        Extract surrounding context for a code snippet.

        Args:
            tag: BeautifulSoup tag containing the code

        Returns:
            Surrounding context text
        """
        # Get previous siblings (headings, paragraphs)
        context_parts = []

        # Look for previous heading
        prev = tag.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
        if prev:
            context_parts.append(prev.get_text().strip())

        # Look for previous paragraph
        prev_p = tag.find_previous("p")
        if prev_p:
            context_parts.append(prev_p.get_text().strip())

        return " ".join(context_parts) if context_parts else None

    def _score_snippet(self, snippet: CodeSnippet) -> None:
        """
        Score a code snippet based on quality metrics.

        Modifies the snippet in place with scores.

        Args:
            snippet: Code snippet to score
        """
        content = snippet.content

        # Code Quality Score (0-1)
        quality_score = 0.0

        # Has imports/requires (good for understanding dependencies)
        if re.search(
            r"^(?:import|from|require|include|using)\s+", content, re.MULTILINE | re.IGNORECASE
        ):
            quality_score += 0.2

        # Has function definitions
        if re.search(
            r"^(?:def|function|fn|func|class|public|private)\s+", content, re.MULTILINE
        ):
            quality_score += 0.2

        # Has comments/documentation
        if re.search(r"(?://|#|/\*|\"\"\"|''')", content):
            quality_score += 0.2

        # Reasonable length (not too short, not too long)
        line_count = len(content.split("\n"))
        if 5 <= line_count <= 50:
            quality_score += 0.2
        elif line_count > 50:
            quality_score += 0.1

        # Has typical code structure (braces, parentheses, etc.)
        if re.search(r"[{}\[\]()]", content):
            quality_score += 0.2

        snippet.code_quality_score = min(quality_score, 1.0)

        # Formatting Score (0-1)
        formatting_score = 0.0

        # Consistent indentation
        lines = content.split("\n")
        indent_pattern = None
        consistent = True
        for line in lines:
            if not line.strip():
                continue
            match = re.match(r"^(\s+)", line)
            if match:
                indent = match.group(1)
                if indent_pattern is None:
                    indent_pattern = indent
                # Check if it's a multiple of the first indent
                if len(indent) % len(indent_pattern) != 0:
                    consistent = False
                    break

        if consistent:
            formatting_score += 0.5

        # No excessively long lines
        max_line_length = max(len(line) for line in lines) if lines else 0
        if max_line_length <= 100:
            formatting_score += 0.3
        elif max_line_length <= 120:
            formatting_score += 0.2

        # Proper spacing around operators
        if re.search(r"\s[+\-*/=<>]=?\s", content):
            formatting_score += 0.2

        snippet.formatting_score = min(formatting_score, 1.0)

        # Metadata Score (0-1) - based on context availability
        metadata_score = 0.0

        if snippet.language:
            metadata_score += 0.3

        if snippet.context:
            metadata_score += 0.4
            # Extra points if context is a heading
            if snippet.context.strip().startswith(("#", "=")):
                metadata_score += 0.3

        snippet.metadata_score = min(metadata_score, 1.0)

        # Initialization Score (0-1) - indicates if this shows how to get started
        initialization_score = 0.0

        # Keywords suggesting initialization/setup
        init_keywords = [
            "install",
            "setup",
            "initialize",
            "init",
            "getting started",
            "quick start",
            "example",
            "usage",
            "basic",
            "simple",
        ]

        context_lower = (snippet.context or "").lower()
        content_lower = content.lower()

        for keyword in init_keywords:
            if keyword in context_lower:
                initialization_score += 0.3
            if keyword in content_lower:
                initialization_score += 0.2

        # Has main/entry point
        if re.search(r"if\s+__name__\s*==\s*['\"]__main__['\"]", content):
            initialization_score += 0.3

        # Has basic instantiation patterns
        if re.search(r"new\s+\w+|=\s*\w+\(", content):
            initialization_score += 0.2

        snippet.initialization_score = min(initialization_score, 1.0)
