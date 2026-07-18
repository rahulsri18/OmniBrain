"""
qdrant_client.py

Handles all interactions with the Qdrant vector database.
"""

import os
from uuid import uuid4
from typing import List, Dict, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


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

        self.client = QdrantClient(host=host, port=port)
        
        # 🚀 क्लास बनते ही कलेक्शन अपने आप चेक और क्रिएट हो जाएगा
        self.setup_collection()

    def setup_collection(self):
        """
        Create collection if it doesn't already exist.
        """
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

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )
        print(f"Successfully inserted {len(points)} vectors into Qdrant.")

    def search(self, query_embedding: List[float], limit: int = 5):
        """
        Search similar vectors.
        """
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=limit,
        )
        return results.points

    def delete_collection(self):
        """
        Delete collection.
        """
        self.client.delete_collection(collection_name=self.collection_name)
        print("Collection deleted.")