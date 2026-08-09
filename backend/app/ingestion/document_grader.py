"""
document_grader.py

Grades retrieved chunks for relevance to a user query before they're
passed to the generation step of the RAG pipeline.
"""

import asyncio
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any

GRADER_PROMPT_VERSION = "v1.0"
DEFAULT_GRADER_MODEL = "claude-sonnet-4-6"

GRADER_SYSTEM_PROMPT = """You are a document relevance grader for a retrieval-augmented generation (RAG) system.

Your ONLY job is to judge whether a retrieved document chunk is relevant to a user's question. You do NOT answer the question. You do NOT use outside knowledge. You do NOT explain your reasoning beyond what is requested below.

A chunk is RELEVANT if it contains information, facts, or context that would help answer the user's question — even partially. A chunk is NOT RELEVANT if it only shares surface keywords with the question but does not actually help answer it, or if it is about a different topic entirely.

Respond with ONLY a JSON object in this exact format, and nothing else:

{"relevant": true or false, "score": <float between 0.0 and 1.0>, "reason": "<one short sentence>"}

Do not include markdown code fences, preamble, or any text outside the JSON object.
"""

GRADER_USER_TEMPLATE = """User Question:
{question}

Retrieved Document Chunk:
{chunk}
"""


@dataclass
class GradeResult:
    relevant: bool
    score: float
    reason: str
    ungraded: bool = False


class DocumentGrader:
    def __init__(
        self,
        llm_client: Any = None,
        model: str | None = None,
        call_fn: Any | None = None,
        relevance_threshold: float = 0.5,
        max_retries: int = 2,
        retry_backoff_seconds: float = 1.0,
        request_timeout: float | None = 10.0,
        on_ungraded: str = "not_relevant",
    ):
        if llm_client is None and call_fn is None:
            raise ValueError("Provide either llm_client or call_fn")
        if on_ungraded not in ("not_relevant", "relevant", "raise"):
            raise ValueError(
                "on_ungraded must be 'not_relevant', 'relevant', or 'raise'"
            )

        self.llm_client = llm_client
        self.model = model or os.environ.get("GRADER_MODEL", DEFAULT_GRADER_MODEL)
        self.call_fn = call_fn
        self.relevance_threshold = relevance_threshold
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self.request_timeout = request_timeout
        self.on_ungraded = on_ungraded

    def _call_llm(self, question: str, chunk_text: str) -> str:
        """Call the LLM with retries on transient failures."""
        user_prompt = GRADER_USER_TEMPLATE.format(question=question, chunk=chunk_text)

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                if self.call_fn is not None:
                    return self.call_fn(GRADER_SYSTEM_PROMPT, user_prompt)

                kwargs: dict[str, Any] = {
                    "model": self.model,
                    "max_tokens": 200,
                    "system": GRADER_SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_prompt}],
                }
                if self.request_timeout is not None:
                    kwargs["timeout"] = self.request_timeout

                response = self.llm_client.messages.create(**kwargs)
                for block in response.content:
                    if getattr(block, "type", None) == "text":
                        return block.text
                return ""
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(self.retry_backoff_seconds * (2**attempt))
                    continue
                raise last_error

    @staticmethod
    def _parse_grade(raw_text: str) -> GradeResult:
        cleaned = raw_text.strip()
        cleaned = re.sub(r"^```(json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            return GradeResult(
                relevant=False, score=0.0, reason="unparsable_grader_output"
            )

        try:
            data = json.loads(match.group(0))
            raw_score = float(data.get("score", 0.0))
            score = min(1.0, max(0.0, raw_score))
            return GradeResult(
                relevant=bool(data.get("relevant", False)),
                score=score,
                reason=str(data.get("reason", "")),
            )
        except (json.JSONDecodeError, TypeError, ValueError):
            return GradeResult(
                relevant=False, score=0.0, reason="unparsable_grader_output"
            )

    @staticmethod
    def _extract_chunk_text(doc: dict[str, Any]) -> str:
        payload = doc.get("payload") or {}
        return (
            payload.get("text")
            or payload.get("content")
            or payload.get("chunk")
            or doc.get("text", "")
        )

    def grade_one(self, question: str, doc: dict[str, Any]) -> dict[str, Any]:
        """Grade a single retrieved document dict synchronously."""
        chunk_text = self._extract_chunk_text(doc)

        if not chunk_text.strip():
            grade = GradeResult(relevant=False, score=0.0, reason="empty_chunk")
        else:
            try:
                raw = self._call_llm(question, chunk_text)
                grade = self._parse_grade(raw)
            except Exception as exc:
                if self.on_ungraded == "raise":
                    raise
                fallback_relevant = self.on_ungraded == "relevant"
                grade = GradeResult(
                    relevant=fallback_relevant,
                    score=1.0 if fallback_relevant else 0.0,
                    reason=f"ungraded_llm_error: {exc}",
                    ungraded=True,
                )

        return {
            **doc,
            "relevant": grade.relevant and grade.score >= self.relevance_threshold,
            "relevance_score": grade.score,
            "relevance_reason": grade.reason,
            "relevance_ungraded": grade.ungraded,
            "grader_prompt_version": GRADER_PROMPT_VERSION,
        }

    def grade_batch(
        self, question: str, docs: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Synchronous batch grading."""
        return [self.grade_one(question, doc) for doc in docs]

    async def agrade_batch(
        self, question: str, docs: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Async batch grading running doc evaluations concurrently."""
        loop = asyncio.get_running_loop()
        tasks = [
            loop.run_in_executor(None, self.grade_one, question, doc) for doc in docs
        ]
        return await asyncio.gather(*tasks)
