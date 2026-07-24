"""Post-search deduplication for retrieval results."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Sequence


class TextDeduplicator:
    """Remove duplicate retrieval results that share the same normalized text."""

    def __init__(self, case_sensitive: bool = False, sort_results: bool = True):
        self.case_sensitive = case_sensitive
        self.sort_results = sort_results

    def _get_payload(self, result: Any) -> dict[str, Any] | None:
        if isinstance(result, dict):
            payload = result.get("payload")
            return payload if isinstance(payload, dict) else None

        payload = getattr(result, "payload", None)
        return payload if isinstance(payload, dict) else None

    def _get_score(self, result: Any) -> float | None:
        if isinstance(result, dict):
            score = result.get("score")
        else:
            score = getattr(result, "score", None)

        if score is None:
            return None

        try:
            return float(score)
        except (TypeError, ValueError):
            return None

    def _get_text(self, result: Any) -> str | None:
        payload = self._get_payload(result)
        if not payload:
            return None

        text = payload.get("text")
        if text is None:
            return None

        return text if isinstance(text, str) else str(text)

    def _normalize_text(self, text: str) -> str:
        normalized = re.sub(r"\s+", " ", text).strip()
        if not self.case_sensitive:
            normalized = normalized.casefold()
        return normalized

    def _fingerprint(self, text: str) -> str:
        normalized = self._normalize_text(text)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def deduplicate(self, results: Sequence[Any] | None) -> list[Any]:
        """Keep the best-scoring result for each normalized text fingerprint."""
        unique_by_text: dict[str, Any] = {}
        passthrough: list[Any] = []

        for result in results or []:
            text = self._get_text(result)
            if not text:
                passthrough.append(result)
                continue

            fingerprint = self._fingerprint(text)
            score = self._get_score(result)
            existing = unique_by_text.get(fingerprint)

            if existing is None:
                unique_by_text[fingerprint] = result
                continue

            existing_score = self._get_score(existing)
            if score is not None and (existing_score is None or score > existing_score):
                unique_by_text[fingerprint] = result

        deduped = list(unique_by_text.values()) + passthrough

        if not self.sort_results:
            return deduped

        return sorted(
            deduped,
            key=lambda item: (
                self._get_score(item) is not None,
                self._get_score(item) if self._get_score(item) is not None else float("-inf"),
            ),
            reverse=True,
        )