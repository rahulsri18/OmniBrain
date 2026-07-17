from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


class QdrantDB:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
    ):
        self.client = QdrantClient(
            host=host,
            port=port,
        )

    def create_collection(
        self,
        collection_name: str,
        vector_size: int,
    ):
        collections = self.client.get_collections().collections

        existing = [c.name for c in collections]

        if collection_name not in existing:

            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )

            print(f"{collection_name} created.")

        else:

            print(f"{collection_name} already exists.")