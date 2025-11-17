"""LLM-based content enrichment for code snippets and documentation."""

import json
from typing import List, Optional

import httpx

from docvector.core import get_logger, settings

logger = get_logger(__name__)


class ContentEnricher:
    """Enriches content with LLM-generated metadata and explanations."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize the content enricher.

        Args:
            api_key: OpenAI API key (defaults to settings)
            model: OpenAI model to use (defaults to gpt-4o-mini for cost efficiency)
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"

    async def enrich_code_snippet(
        self,
        code: str,
        language: Optional[str] = None,
        context: Optional[str] = None,
    ) -> dict:
        """
        Enrich a code snippet with LLM-generated explanation and topics.

        Args:
            code: The code snippet
            language: Programming language
            context: Surrounding context/documentation

        Returns:
            Dictionary with enrichment data:
                - explanation: Brief explanation of what the code does
                - topics: List of relevant topics/concepts
        """
        # Build prompt
        prompt_parts = []

        if context:
            prompt_parts.append(f"Context: {context}\n")

        prompt_parts.append(f"Code ({language or 'unknown'}):\n```\n{code}\n```\n")

        prompt_parts.append(
            "Provide a brief 1-2 sentence explanation of what this code does. "
            "Also extract 3-5 relevant topic tags (e.g., 'database', 'authentication', 'async')."
        )

        prompt = "\n".join(prompt_parts)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "You are a code documentation assistant. "
                                    "Provide concise explanations and topic tags. "
                                    "Respond in JSON format with keys: explanation, topics."
                                ),
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.3,
                        "response_format": {"type": "json_object"},
                    },
                )

                if response.status_code != 200:
                    logger.error(
                        f"OpenAI API error: {response.status_code} - {response.text}",
                    )
                    return {"explanation": None, "topics": []}

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                result = json.loads(content)

                return {
                    "explanation": result.get("explanation", ""),
                    "topics": result.get("topics", []),
                }

        except Exception as e:
            logger.error(f"Error enriching code snippet: {e}")
            return {"explanation": None, "topics": []}

    async def enrich_text_chunk(self, text: str, title: Optional[str] = None) -> dict:
        """
        Enrich a text chunk with LLM-generated topics and summary.

        Args:
            text: The text chunk
            title: Document/section title

        Returns:
            Dictionary with enrichment data:
                - summary: Brief summary (optional)
                - topics: List of relevant topics
        """
        # Build prompt
        prompt_parts = []

        if title:
            prompt_parts.append(f"Title: {title}\n")

        prompt_parts.append(f"Text:\n{text[:1000]}\n")  # Limit to first 1000 chars

        prompt_parts.append(
            "Extract 3-5 relevant topic tags that describe this content "
            "(e.g., 'getting started', 'configuration', 'API reference')."
        )

        prompt = "\n".join(prompt_parts)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "You are a documentation assistant. "
                                    "Extract topic tags from technical documentation. "
                                    "Respond in JSON format with key: topics (array)."
                                ),
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.3,
                        "response_format": {"type": "json_object"},
                    },
                )

                if response.status_code != 200:
                    logger.error(
                        f"OpenAI API error: {response.status_code} - {response.text}",
                    )
                    return {"topics": []}

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                result = json.loads(content)

                return {"topics": result.get("topics", [])}

        except Exception as e:
            logger.error(f"Error enriching text chunk: {e}")
            return {"topics": []}

    async def batch_enrich_snippets(
        self,
        snippets: List[dict],
        batch_size: int = 5,
    ) -> List[dict]:
        """
        Enrich multiple code snippets in batches.

        Args:
            snippets: List of snippet dictionaries with 'code', 'language', 'context'
            batch_size: Number of snippets to process concurrently

        Returns:
            List of enriched snippets
        """
        import asyncio

        enriched = []

        for i in range(0, len(snippets), batch_size):
            batch = snippets[i : i + batch_size]
            tasks = [
                self.enrich_code_snippet(
                    code=s.get("code", ""),
                    language=s.get("language"),
                    context=s.get("context"),
                )
                for s in batch
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for snippet, result in zip(batch, results):
                if isinstance(result, Exception):
                    logger.error(f"Error enriching snippet: {result}")
                    snippet["enrichment"] = None
                    snippet["topics"] = []
                else:
                    snippet["enrichment"] = result.get("explanation")
                    snippet["topics"] = result.get("topics", [])

                enriched.append(snippet)

        return enriched
