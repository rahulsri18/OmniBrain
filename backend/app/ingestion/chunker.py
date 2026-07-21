"""
chunker.py

Optimized utility module for splitting extracted PDF text into
overlapping chunks for embedding generation and retrieval.
"""

import os
import os
from typing import List, Dict

from langchain_text_splitters import RecursiveCharacterTextSplitter


class TextChunker:
    """
    Splits large documents into smaller overlapping chunks
    optimized for Retrieval-Augmented Generation (RAG).
    """

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        min_chunk_length: int = 30,
    ):
        """
        Args:
            chunk_size: Maximum size of each chunk.
            chunk_overlap: Number of overlapping characters.
            min_chunk_length: Ignore chunks smaller than this.
        """
        self.chunk_size = chunk_size or int(os.getenv("CHUNK_SIZE", "800"))
        self.chunk_overlap = chunk_overlap or int(os.getenv("CHUNK_OVERLAP", "120"))
        self.min_chunk_length = min_chunk_length

        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0.")

        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative.")

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size."
            )


        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=[
                "\n\n",
                "\n",
                ". ",
                "? ",
                "! ",
                "; ",
                ", ",
                " ",
                "",
            ],
            keep_separator=True,
        )

    def split_text(self, text: str) -> List[str]:
        """
        Split a single document into optimized chunks.
        """

        if not text or not text.strip():
            return []

        chunks = self.text_splitter.split_text(text)

        # Remove whitespace
        chunks = [chunk.strip() for chunk in chunks]

        # Remove tiny chunks
        chunks = [
            chunk
            for chunk in chunks
            if len(chunk) >= self.min_chunk_length
        ]

        return chunks

    def split_documents(self, documents: List[str]) -> List[str]:
        """
        Split multiple documents into chunks.
        """

        all_chunks = []

        for document in documents:
            all_chunks.extend(self.split_text(document))

        return all_chunks

    def overlap_percentage(self) -> float:
        """
        Return overlap percentage.
        """

        return round(
            (self.chunk_overlap / self.chunk_size) * 100,
            2,
        )

    def get_chunk_statistics(
        self,
        chunks: List[str],
    ) -> Dict:
        """
        Return useful statistics.
        """

        if not chunks:
            return {
                "total_chunks": 0,
                "average_chunk_length": 0,
                "largest_chunk": 0,
                "smallest_chunk": 0,
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "overlap_percentage": self.overlap_percentage(),
            }

        lengths = [len(chunk) for chunk in chunks]

        return {
            "total_chunks": len(chunks),
            "average_chunk_length": round(
                sum(lengths) / len(lengths),
                2,
            ),
            "largest_chunk": max(lengths),
            "smallest_chunk": min(lengths),
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "overlap_percentage": self.overlap_percentage(),
        }

    def print_statistics(self, chunks: List[str]) -> None:
        """
        Print chunk statistics.
        """

        stats = self.get_chunk_statistics(chunks)

        print("\n========== Chunk Statistics ==========")
        print(f"Total Chunks        : {stats['total_chunks']}")
        print(f"Chunk Size          : {stats['chunk_size']}")
        print(f"Chunk Overlap       : {stats['chunk_overlap']}")
        print(f"Overlap Percentage  : {stats['overlap_percentage']}%")
        print(f"Average Length      : {stats['average_chunk_length']}")
        print(f"Largest Chunk       : {stats['largest_chunk']}")
        print(f"Smallest Chunk      : {stats['smallest_chunk']}")
        print("======================================\n")