"""
qdrant_client.py

Handles all interactions with the Qdrant vector database.
"""

import os
from uuid import uuid4
from typing import List, Dict, Optional

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        FieldCondition,
        Filter,
        MatchValue,
        PointStruct,
        Range,
        VectorParams,
    )
except Exception:
    QdrantClient = None
    Distance = None
    FieldCondition = None
    Filter = None
    MatchValue = None
    VectorParams = None
    PointStruct = None
    Range = None
    _MISSING_QDRANT_MSG = (
        "qdrant-client package is not installed. Install with: pip install qdrant-client"
    )


class QdrantDB:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: Optional[str] = None,
        vector_size: Optional[int] = None,
    ):
        # .env से वैल्यू उठाएगा, नहीं तो लोकल मॉडल का डिफॉल्ट (384) लेगा
        self.collection_name = collection_name or os.getenv("COLLECTION_NAME", "omnibrain")
        self.vector_size = vector_size or int(os.getenv("VECTOR_SIZE", "384"))

        if QdrantClient is None:
            # Keep object alive for development runs; methods will raise if used.
            self.client = None
            print(_MISSING_QDRANT_MSG)
        else:
            self.client = QdrantClient(host=host, port=port)

        # Only attempt to setup collection if qdrant-client is available
        if self.client is not None:
            self.setup_collection()

    def setup_collection(self):
        """
        Create collection if it doesn't already exist.
        """
        if self.client is None:
            raise RuntimeError(_MISSING_QDRANT_MSG)

        try:
            collections = self.client.get_collections().collections
            names = [c.name for c in collections]

            if self.collection_name not in names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE,
                    ),
                )
                print(f"Collection '{self.collection_name}' created successfully.")
            else:
                print(f"Collection '{self.collection_name}' already exists.")
        except Exception as e:
            print(f"Error setting up Qdrant collection: {e}")

    def insert_vectors(
        self,
        chunks: List[str],
        embeddings: List[List[float]],
        metadata: Optional[List[Dict]] = None,
        collection_name: Optional[str] = None,
    ):
        """
        Insert vectors into Qdrant.
        """
        points = []
        

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            payload = {"text": chunk}

            if metadata and i < len(metadata):
                payload.update(metadata[i])

            point = PointStruct(
                id=str(uuid4()),
                vector=embedding,
                payload=payload,
            )
            points.append(point)

        if self.client is None:
            raise RuntimeError(_MISSING_QDRANT_MSG)

        self.client.upsert(
            collection_name=collection_name or self.collection_name,
            points=points,
        )
        print(f"Successfully inserted {len(points)} vectors into Qdrant.")

    def _build_page_filter(
        self,
        page_number: Optional[int] = None,
        page_numbers: Optional[List[int]] = None,
        page_range: Optional[tuple[int, int]] = None,
    ):
        if page_range is not None:
            if Filter is None or FieldCondition is None or Range is None:
                raise RuntimeError(_MISSING_QDRANT_MSG)

            start_page, end_page = page_range
            return Filter(
                must=[
                    FieldCondition(
                        key="page_number",
                        range=Range(gte=start_page, lte=end_page),
                    )
                ]
            )

        page_values = list(page_numbers or [])
        if page_number is not None:
            page_values.append(page_number)

        if not page_values:
            return None

        if Filter is None or FieldCondition is None or MatchValue is None:
            raise RuntimeError(_MISSING_QDRANT_MSG)

        if len(page_values) == 1:
            return Filter(
                must=[
                    FieldCondition(
                        key="page_number",
                        match=MatchValue(value=page_values[0]),
                    )
                ]
            )

        return Filter(
            should=[
                FieldCondition(
                    key="page_number",
                    match=MatchValue(value=value),
                )
                for value in page_values
            ]
        )

    def search(
        self,
        query_embedding,
        limit=5,
        collection_name=None,
        page: Optional[int] = None,
        page_number: Optional[int] = None,
        page_numbers: Optional[List[int]] = None,
        page_range: Optional[tuple[int, int]] = None,
    ):
        """
        Search similar vectors.
        """
        if self.client is None:
            raise RuntimeError(_MISSING_QDRANT_MSG)

        if page_number is None:
            page_number = page

        query_filter = self._build_page_filter(
            page_number=page_number,
            page_numbers=page_numbers,
            page_range=page_range,
        )

        results = self.client.query_points(
            collection_name=collection_name or self.collection_name,
            query=query_embedding,
            limit=limit,
            query_filter=query_filter,
        )
        return results.points

    def delete_collection(self):
        """
        Delete collection.
        """
        if self.client is None:
            raise RuntimeError(_MISSING_QDRANT_MSG)

        self.client.delete_collection(collection_name=self.collection_name)
        print("Collection deleted.")

    def create_collection(self, collection_name: str, vector_size: int):
        """
        Create a new Qdrant collection if it doesn't already exist.
        """
        try:
            if self.client is None:
                raise RuntimeError(_MISSING_QDRANT_MSG)

            collections = self.client.get_collections().collections
            names = [c.name for c in collections]

            if collection_name not in names:

                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE,
                    ),
                )

                print(f"Collection '{collection_name}' created successfully.")

            else:
                print(f"Collection '{collection_name}' already exists.")

        except Exception as e:
            print(f"Error creating collection '{collection_name}': {e}")