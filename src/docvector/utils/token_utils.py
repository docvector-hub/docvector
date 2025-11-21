"""Token counting and limiting utilities."""

import re
from typing import List


class TokenLimiter:
    """Utility for limiting text to a specific token count."""

    def __init__(self, tokens_per_word: float = 1.3):
        """
        Initialize the token limiter.

        Args:
            tokens_per_word: Approximate tokens per word ratio (default 1.3 for GPT models)
        """
        self.tokens_per_word = tokens_per_word

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        This is an approximation. For exact counts, use tiktoken library.

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """
        # Simple approximation: split on whitespace and multiply by ratio
        words = len(text.split())
        return int(words * self.tokens_per_word)

    def truncate_to_tokens(
        self,
        text: str,
        max_tokens: int,
        preserve_sentences: bool = True,
    ) -> str:
        """
        Truncate text to fit within token limit.

        Args:
            text: Text to truncate
            max_tokens: Maximum number of tokens
            preserve_sentences: If True, truncate at sentence boundaries

        Returns:
            Truncated text
        """
        current_tokens = self.count_tokens(text)

        if current_tokens <= max_tokens:
            return text

        # Estimate how much to keep
        ratio = max_tokens / current_tokens
        target_chars = int(len(text) * ratio)

        if preserve_sentences:
            # Find sentence boundaries
            sentences = re.split(r'(?<=[.!?])\s+', text)
            truncated = ""
            current_tokens = 0

            for sentence in sentences:
                sentence_tokens = self.count_tokens(sentence)
                if current_tokens + sentence_tokens <= max_tokens:
                    truncated += sentence + " "
                    current_tokens += sentence_tokens
                else:
                    break

            return truncated.strip()
        else:
            # Simple truncation
            truncated = text[:target_chars]
            # Try to end at word boundary
            last_space = truncated.rfind(' ')
            if last_space > 0:
                truncated = truncated[:last_space]

            return truncated + "..."

    def limit_results_to_tokens(
        self,
        results: List[dict],
        max_tokens: int,
        content_key: str = "content",
    ) -> List[dict]:
        """
        Limit a list of results to fit within token budget.

        Args:
            results: List of result dictionaries
            max_tokens: Maximum total tokens
            content_key: Key in result dict containing the text content

        Returns:
            Truncated list of results
        """
        limited = []
        current_tokens = 0

        for result in results:
            content = result.get(content_key, "")
            result_tokens = self.count_tokens(content)

            if current_tokens + result_tokens <= max_tokens:
                limited.append(result)
                current_tokens += result_tokens
            else:
                # Try to include partial result
                remaining_tokens = max_tokens - current_tokens
                if remaining_tokens > 50:  # Only include if significant space left
                    truncated_content = self.truncate_to_tokens(
                        content,
                        remaining_tokens,
                        preserve_sentences=True,
                    )
                    truncated_result = result.copy()
                    truncated_result[content_key] = truncated_content
                    truncated_result["truncated"] = True
                    limited.append(truncated_result)

                break

        return limited


class TikTokenCounter:
    """More accurate token counter using tiktoken library."""

    def __init__(self, encoding_name: str = "cl100k_base"):
        """
        Initialize with tiktoken encoding.

        Args:
            encoding_name: Encoding to use (cl100k_base for GPT-4, GPT-3.5-turbo)
        """
        try:
            import tiktoken

            self.encoding = tiktoken.get_encoding(encoding_name)
            self.available = True
        except ImportError:
            self.encoding = None
            self.available = False

    def count_tokens(self, text: str) -> int:
        """
        Count exact tokens using tiktoken.

        Args:
            text: Text to count tokens for

        Returns:
            Exact token count
        """
        if not self.available:
            # Fallback to approximation
            limiter = TokenLimiter()
            return limiter.count_tokens(text)

        return len(self.encoding.encode(text))

    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to exact token count.

        Args:
            text: Text to truncate
            max_tokens: Maximum number of tokens

        Returns:
            Truncated text
        """
        if not self.available:
            # Fallback to approximation
            limiter = TokenLimiter()
            return limiter.truncate_to_tokens(text, max_tokens)

        tokens = self.encoding.encode(text)

        if len(tokens) <= max_tokens:
            return text

        # Decode truncated tokens
        truncated_tokens = tokens[:max_tokens]
        return self.encoding.decode(truncated_tokens)
