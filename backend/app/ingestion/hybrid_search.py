"""
hybrid_search.py

Hybrid text+image retriever that queries Qdrant for both
semantic text matches and CLIP text->image matches.

Usage: create `HybridRetriever()` and call `retrieve(query, ...)`.
"""
from typing import List, Dict, Any

import torch
from transformers import CLIPProcessor, CLIPModel

from .embedding import EmbeddingGenerator
from .deduplication import TextDeduplicator
from .retrieval_filter import RetrievalFilter
from ..vectordb.qdrant_client import QdrantDB
from ..logger import logger


class HybridRetriever:
    def __init__(
        self,
        text_collection: str = None,
        image_collection: str = None,
        clip_model_name: str = "openai/clip-vit-base-patch32",
    ):
        """Initialize text embedder, CLIP model and Qdrant client.

        - `text_collection` defaults to the QdrantDB default (omnibrain)
        - `image_collection` defaults to 'omnibrain_vision'
        """
        self.embedder = EmbeddingGenerator()

        # CLIP for text->image retrieval
        self.clip_model_name = clip_model_name
        self.processor = CLIPProcessor.from_pretrained(self.clip_model_name)
        self.clip_model = CLIPModel.from_pretrained(self.clip_model_name)

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.clip_model.to(self.device)

        self.retrieval_filter = RetrievalFilter()
        self.deduplicator = TextDeduplicator()

        # Qdrant DB client (single instance can query multiple collections)
        self.db = QdrantDB()
        self.text_collection = text_collection or self.db.collection_name
        self.image_collection = image_collection or "omnibrain_vision"

    def _point_to_dict(self, point: Any) -> Dict[str, Any]:
        """Normalize a returned Qdrant point to a dict.

        Supports both attribute objects and plain dicts.
        """
        try:
            pid = getattr(point, "id", None)
            if pid is None and isinstance(point, dict):
                pid = point.get("id")

            payload = getattr(point, "payload", None)
            if payload is None and isinstance(point, dict):
                payload = point.get("payload")

            score = getattr(point, "score", None)
            if score is None and isinstance(point, dict):
                score = point.get("score")
        except Exception:
            pid = point.get("id") if isinstance(point, dict) else None
            payload = point.get("payload") if isinstance(point, dict) else None
            score = point.get("score") if isinstance(point, dict) else None

        return {"id": pid, "payload": payload, "score": score}

    def search_text(
        self,
        query: str,
        top_k: int = 5,
        page: int | None = None,
        page_number: int | None = None,
        page_numbers: list[int] | None = None,
        page_range: tuple[int, int] | None = None,
    ) -> List[Dict[str, Any]]:
        """Generate a text embedding and search the text collection."""
        if not query or not query.strip():
            return []

        emb = self.embedder.generate_embedding(query)
        if not emb:
            return []

        try:
            results = self.db.search(
                query_embedding=emb,
                limit=top_k,
                collection_name=self.text_collection,
                page=page,
                page_number=page_number,
                page_numbers=page_numbers,
                page_range=page_range,
            )
            return [self._point_to_dict(p) for p in results]
        except Exception as e:
            logger.error(f"Text search failed: {e}")
            return []

    def search_images(
        self,
        query: str,
        top_k: int = 5,
        page: int | None = None,
        page_number: int | None = None,
        page_numbers: list[int] | None = None,
        page_range: tuple[int, int] | None = None,
    ) -> List[Dict[str, Any]]:
        """Generate a CLIP text embedding and search the image collection."""
        if not query or not query.strip():
            return []

        try:
            inputs = self.processor(text=[query], return_tensors="pt", padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                text_out = self.clip_model.get_text_features(**inputs)

            # `get_text_features` may return a Tensor or a ModelOutput depending on HF version.
            if isinstance(text_out, torch.Tensor):
                text_feats = text_out
            else:
                # try common attributes
                if hasattr(text_out, "pooler_output") and text_out.pooler_output is not None:
                    text_feats = text_out.pooler_output
                elif hasattr(text_out, "last_hidden_state") and text_out.last_hidden_state is not None:
                    text_feats = text_out.last_hidden_state[:, 0, :]
                else:
                    # fallback: try to convert to tensor
                    text_feats = torch.tensor(text_out)

            # normalize
            text_feats = text_feats / text_feats.norm(dim=-1, keepdim=True)
            emb = text_feats.cpu().numpy()[0].tolist()

            try:
                results = self.db.search(
                    query_embedding=emb,
                    limit=top_k,
                    collection_name=self.image_collection,
                    page=page,
                    page_number=page_number,
                    page_numbers=page_numbers,
                    page_range=page_range,
                )
                return [self._point_to_dict(p) for p in results]
            except Exception as qe:
                # If the image collection does not exist, create it (empty) so future ingestions can populate it.
                err = str(qe)
                if "doesn't exist" in err or "not found" in err.lower():
                    logger.info(f"Image collection '{self.image_collection}' not found. Creating empty collection.")
                    try:
                        # CLIP embeddings are 512-dim
                        self.db.create_collection(collection_name=self.image_collection, vector_size=512)
                    except Exception as ce:
                        logger.error(f"Failed to create image collection: {ce}")
                else:
                    logger.error(f"Image search (CLIP) failed: {qe}")

                return []
        except Exception as e:
            logger.error(f"Image search (CLIP) failed: {e}")
            return []

    def retrieve(
        self,
        query: str,
        top_k_text: int = 5,
        top_k_images: int = 5,
        page: int | None = None,
        page_number: int | None = None,
        page_numbers: list[int] | None = None,
        page_range: tuple[int, int] | None = None,
    ) -> Dict[str, Any]:
        """Run both text and image retrieval and return merged response."""
        if page_number is None:
            page_number = page

        raw_text_matches = self.search_text(
            query,
            top_k=top_k_text,
            page_number=page_number,
            page_numbers=page_numbers,
            page_range=page_range,
        )
        raw_image_matches = self.search_images(
            query,
            top_k=top_k_images,
            page_number=page_number,
            page_numbers=page_numbers,
            page_range=page_range,
        )

        text_matches = self.deduplicator.deduplicate(
            self.retrieval_filter.filter_results(raw_text_matches)
        )
        image_matches = self.deduplicator.deduplicate(
            self.retrieval_filter.filter_results(raw_image_matches)
        )

        # Merge by score (if available) into a single list for convenience.
        merged = []
        for t in text_matches:
            merged.append({"type": "text", **t})
        for im in image_matches:
            merged.append({"type": "image", **im})

        merged = self.deduplicator.deduplicate(merged)

        # Sort by score (descending). Missing scores go to the end.
        merged_sorted = sorted(
            merged,
            key=lambda x: (x.get("score") is not None, x.get("score") if x.get("score") is not None else -9999),
            reverse=True,
        )

        return {
            "query": query,
            "page": page_number,
            "page_number": page_number,
            "page_numbers": page_numbers,
            "page_range": page_range,
            "text_matches": text_matches,
            "image_matches": image_matches,
            "merged": merged_sorted,
        }


if __name__ == "__main__":
    # Quick manual test when run as a script. Replace the sample question below
    # with something relevant to your Qdrant data.
    retriever = HybridRetriever()
    sample_questions = [
        "What is the main model used for text embeddings?",
        "Show charts about model performance",
    ]

    for q in sample_questions:
        print("\n=== Query:", q)
        res = retriever.retrieve(q, top_k_text=3, top_k_images=3)
        print("Text matches:")
        for t in res["text_matches"]:
            print(" -", t.get("id"), t.get("payload") or {})
        print("Image matches:")
        for im in res["image_matches"]:
            print(" -", im.get("id"), im.get("payload") or {})
        print("Merged:")
        for m in res["merged"]:
            print(" -", m.get("type"), m.get("id"), m.get("score"))
