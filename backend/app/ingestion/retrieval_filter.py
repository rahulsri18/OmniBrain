"""Post-search filtering for vector retrieval results."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ..config import settings


class RetrievalFilter:
    """Filter Qdrant search results by score threshold."""

    def __init__(self, threshold: float | None = None, sort_results: bool = True):
        self.threshold = float(
            settings.SEARCH_SCORE_THRESHOLD if threshold is None else threshold
        )
        self.sort_results_enabled = sort_results

    def _get_score(self, result: Any) -> float | None:
        if isinstance(result, dict):
            return result.get("score")
        return getattr(result, "score", None)

    def filter_results(self, results: Sequence[Any] | None) -> list[Any]:
        """Keep only results whose score meets or exceeds the threshold."""
        filtered: list[Any] = []

        for result in results or []:
            score = self._get_score(result)
            if score is None:
                continue

            try:
                if float(score) >= self.threshold:
                    filtered.append(result)
            except (TypeError, ValueError):
                continue

        if self.sort_results_enabled:
            return self.sort_results(filtered)

        return filtered

    def sort_results(self, results: Sequence[Any] | None) -> list[Any]:
        """Sort results in descending order by score."""

        def sort_key(result: Any) -> tuple[bool, float]:
            score = self._get_score(result)
            if score is None:
                return (False, float("-inf"))

            try:
                return (True, float(score))
            except (TypeError, ValueError):
                return (False, float("-inf"))

        return sorted(results or [], key=sort_key, reverse=True)
