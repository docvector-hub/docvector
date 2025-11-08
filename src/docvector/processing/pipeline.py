"""Document processing pipeline."""

from typing import Dict, List, Optional

from docvector.core import get_logger, settings

from .chunkers import BaseChunker, FixedSizeChunker, SemanticChunker, TextChunk
from .parsers import BaseParser, HTMLParser, MarkdownParser, ParsedDocument

logger = get_logger(__name__)


class ProcessingPipeline:
    """
    Document processing pipeline.

    Parses documents and chunks them for embedding.
    """

    def __init__(
        self,
        chunking_strategy: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ):
        """
        Initialize processing pipeline.

        Args:
            chunking_strategy: Strategy to use ('fixed', 'semantic')
            chunk_size: Size of chunks
            chunk_overlap: Overlap between chunks
        """
        self.chunking_strategy = chunking_strategy or settings.chunking_strategy
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

        # Initialize parsers
        self.parsers: List[BaseParser] = [
            HTMLParser(),
            MarkdownParser(),
        ]

        # Initialize chunker
        self.chunker = self._create_chunker()

    def _create_chunker(self) -> BaseChunker:
        """Create chunker based on strategy."""
        if self.chunking_strategy == "fixed":
            return FixedSizeChunker(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )
        elif self.chunking_strategy == "semantic":
            return SemanticChunker(
                max_chunk_size=self.chunk_size,
            )
        else:
            logger.warning(
                "Unknown chunking strategy, using fixed",
                strategy=self.chunking_strategy,
            )
            return FixedSizeChunker(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )

    async def process(
        self,
        content: bytes,
        mime_type: str = "text/html",
        url: Optional[str] = None,
        file_extension: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> tuple[ParsedDocument, List[TextChunk]]:
        """
        Process a document: parse and chunk.

        Args:
            content: Raw document content
            mime_type: MIME type of content
            url: Optional URL of document
            file_extension: Optional file extension
            metadata: Optional additional metadata

        Returns:
            Tuple of (parsed document, chunks)
        """
        logger.debug(
            "Processing document",
            mime_type=mime_type,
            url=url,
            size=len(content),
        )

        # Find parser
        parser = self._find_parser(mime_type, file_extension)
        if not parser:
            logger.warning("No parser found, treating as plain text")
            parsed = ParsedDocument(
                content=content.decode("utf-8", errors="ignore"),
                metadata=metadata or {},
            )
        else:
            # Parse document
            parsed = await parser.parse(content, url)

            # Merge metadata
            if metadata:
                if parsed.metadata is None:
                    parsed.metadata = {}
                parsed.metadata.update(metadata)

        # Chunk the parsed text
        chunks = await self.chunker.chunk(parsed.content, parsed.metadata)

        logger.debug(
            "Document processed",
            title=parsed.title,
            chunks=len(chunks),
        )

        return parsed, chunks

    async def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict] = None,
    ) -> List[TextChunk]:
        """
        Chunk text directly without parsing.

        Args:
            text: Text to chunk
            metadata: Optional metadata

        Returns:
            List of chunks
        """
        return await self.chunker.chunk(text, metadata)

    def _find_parser(
        self,
        mime_type: str,
        file_extension: Optional[str],
    ) -> Optional[BaseParser]:
        """Find a parser that can handle the content."""
        for parser in self.parsers:
            if parser.can_parse(mime_type, file_extension):
                return parser

        return None
