# app/ingestion/__init__.py

from .deduplication import TextDeduplicator as TextDeduplicator

__all__ = ["TextDeduplicator"]
