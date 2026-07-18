"""
chunker.py

Utility module for splitting extracted PDF text into
overlapping chunks for embedding generation.
"""

from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter


class TextChunker:
    """
    Splits large documents into smaller overlapping chunks.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                "",
            ],
        )

    def split_text(self, text: str) -> List[str]:
        """
        Split a single text into chunks.

        Args:
            text: Complete document text

        Returns:
            List of text chunks
        """

        if not text.strip():
            return []

        return self.text_splitter.split_text(text)

    def split_documents(self, documents: List[str]) -> List[str]:
        """
        Split multiple documents.

        Args:
            documents: List of complete document texts

        Returns:
            Combined list of chunks
        """

        chunks = []

        for document in documents:
            chunks.extend(
                self.split_text(document)
            )

        return chunks

    def get_chunk_statistics(self, chunks: List[str]) -> dict:
        """
        Return useful statistics about generated chunks.
        """

        if not chunks:
            return {
                "total_chunks": 0,
                "average_chunk_length": 0,
                "largest_chunk": 0,
                "smallest_chunk": 0,
            }

        lengths = [len(chunk) for chunk in chunks]

        return {
            "total_chunks": len(chunks),
            "average_chunk_length": sum(lengths) // len(lengths),
            "largest_chunk": max(lengths),
            "smallest_chunk": min(lengths),
        }