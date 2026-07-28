"""
document_grader.py

Grades retrieved chunks for relevance to a user query before they're
passed to the generation step of the RAG pipeline.

Expected usage inside a retrieval flow (e.g. after HybridRetriever.search_text):

    from document_grader import DocumentGrader

    grader = DocumentGrader(
        llm_client=my_anthropic_client,
        model=None,              # falls back to GRADER_MODEL env var, then a default
        max_retries=2,           # retries transient API errors with backoff
        on_ungraded="not_relevant",  # policy if retries are exhausted
    )
    results = retriever.search_text(query=user_query, top_k=10)
    graded = grader.grade_batch(user_query, results)
    relevant_docs = [r for r in graded if r["relevant"]]
"""

import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


# Bump this whenever GRADER_SYSTEM_PROMPT's wording changes meaningfully.
# Store it alongside grading results/logs so behavior shifts are traceable
# over time (e.g. in an eval dashboard or a "relevance_reason" audit trail).
GRADER_PROMPT_VERSION = "v1.0"

DEFAULT_GRADER_MODEL = "claude-sonnet-4-6"

GRADER_SYSTEM_PROMPT = """You are a document relevance grader for a retrieval-augmented \
generation (RAG) system.

Your ONLY job is to judge whether a retrieved document chunk is relevant to a \
user's question. You do NOT answer the question. You do NOT use outside \
knowledge. You do NOT explain your reasoning beyond what is requested below.

A chunk is RELEVANT if it contains information, facts, or context that would \
help answer the user's question — even partially. A chunk is NOT RELEVANT if \
it only shares surface keywords with the question but does not actually help \
answer it, or if it is about a different topic entirely.

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
    ungraded: bool = False  # True if grading failed after retries (transient error)


class DocumentGrader:
    """
    Wraps an LLM client to grade retrieved chunks for relevance.

    llm_client must expose a `.messages.create(...)`-style method matching
    the Anthropic Python SDK, or you can pass a custom `call_fn` that takes
    (system_prompt, user_prompt) -> str (raw model text) and handles the
    actual API call however you like.
    """

    def __init__(
        self,
        llm_client: Any = None,
        model: Optional[str] = None,
        call_fn: Optional[Any] = None,
        relevance_threshold: float = 0.5,
        max_retries: int = 2,
        retry_backoff_seconds: float = 1.0,
        request_timeout: Optional[float] = 10.0,
        on_ungraded: str = "not_relevant",  # "not_relevant" | "relevant" | "raise"
    ):
        if llm_client is None and call_fn is None:
            raise ValueError("Provide either llm_client or call_fn")
        if on_ungraded not in ("not_relevant", "relevant", "raise"):
            raise ValueError("on_ungraded must be 'not_relevant', 'relevant', or 'raise'")

        self.llm_client = llm_client
        # Model comes from an explicit arg, then env var, then a hardcoded
        # fallback -- so deployments can swap models without a code change.
        self.model = model or os.environ.get("GRADER_MODEL", DEFAULT_GRADER_MODEL)
        self.call_fn = call_fn
        self.relevance_threshold = relevance_threshold
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self.request_timeout = request_timeout
        self.on_ungraded = on_ungraded

    def _call_llm(self, question: str, chunk_text: str) -> str:
        """Call the LLM with retries on transient failures. Raises on exhaustion."""
        user_prompt = GRADER_USER_TEMPLATE.format(question=question, chunk=chunk_text)

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                if self.call_fn is not None:
                    return self.call_fn(GRADER_SYSTEM_PROMPT, user_prompt)

                kwargs: Dict[str, Any] = dict(
                    model=self.model,
                    max_tokens=200,
                    system=GRADER_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                if self.request_timeout is not None:
                    kwargs["timeout"] = self.request_timeout

                response = self.llm_client.messages.create(**kwargs)
                # Anthropic SDK response: response.content is a list of blocks
                for block in response.content:
                    if getattr(block, "type", None) == "text":
                        return block.text
                return ""
            except Exception as exc:  # noqa: BLE001 - deliberately broad, see retry policy
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(self.retry_backoff_seconds * (2 ** attempt))
                    continue
                raise last_error

    @staticmethod
    def _parse_grade(raw_text: str) -> GradeResult:
        """Robustly parse the model's JSON output, tolerating stray text/fences."""
        cleaned = raw_text.strip()
        cleaned = re.sub(r"^```(json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            # Fail safe: treat unparsable output as not relevant, but flag it
            return GradeResult(relevant=False, score=0.0, reason="unparsable_grader_output")

        try:
            data = json.loads(match.group(0))
            raw_score = float(data.get("score", 0.0))
            # The model was asked for 0.0-1.0, but don't trust it blindly --
            # clamp so a stray "score": 5 or a NaN can't silently corrupt
            # downstream ranking/thresholding.
            score = min(1.0, max(0.0, raw_score))
            return GradeResult(
                relevant=bool(data.get("relevant", False)),
                score=score,
                reason=str(data.get("reason", "")),
            )
        except (json.JSONDecodeError, TypeError, ValueError):
            return GradeResult(relevant=False, score=0.0, reason="unparsable_grader_output")

    @staticmethod
    def _extract_chunk_text(doc: Dict[str, Any]) -> str:
        """Pull chunk text out of a hybrid_search-style result dict."""
        payload = doc.get("payload") or {}
        return (
            payload.get("text")
            or payload.get("content")
            or payload.get("chunk")
            or ""
        )

    def grade_one(self, question: str, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Grade a single retrieved document dict (id/payload/score shape)."""
        chunk_text = self._extract_chunk_text(doc)

        if not chunk_text.strip():
            grade = GradeResult(relevant=False, score=0.0, reason="empty_chunk")
        else:
            try:
                raw = self._call_llm(question, chunk_text)
                grade = self._parse_grade(raw)
            except Exception as exc:  # noqa: BLE001 - retries already exhausted upstream
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
            # "score" (above, from the retriever) is the original vector/hybrid
            # search score. "relevance_score" is this grader's own judgment --
            # keep both distinct downstream rather than overwriting one with the other.
            "relevance_score": grade.score,
            "relevance_reason": grade.reason,
            "relevance_ungraded": grade.ungraded,
            "grader_prompt_version": GRADER_PROMPT_VERSION,
        }

    def grade_batch(
        self, question: str, docs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Grade a list of retrieved documents. Returns them annotated in place order."""
        return [self.grade_one(question, doc) for doc in docs]


if __name__ == "__main__":
    # --- Basic smoke test with a fake call_fn (no real API call) ---
    def fake_call_fn(system_prompt: str, user_prompt: str) -> str:
        chunk_section = user_prompt.split("Retrieved Document Chunk:")[-1]
        if "retriev" in chunk_section.lower() or "rag" in chunk_section.lower():
            return '{"relevant": true, "score": 0.9, "reason": "Chunk directly explains RAG."}'
        return '{"relevant": false, "score": 0.1, "reason": "Chunk is off-topic."}'

    grader = DocumentGrader(call_fn=fake_call_fn)

    test_docs = [
        {"id": 1, "payload": {"text": "RAG combines retrieval with generation to ground LLM answers."}, "score": 0.8},
        {"id": 2, "payload": {"text": "Convolutional neural networks are used for image classification."}, "score": 0.6},
    ]

    print("--- basic grading ---")
    for g in grader.grade_batch("What is RAG?", test_docs):
        print(g)

    # --- Score clamping: model misbehaves and returns an out-of-range score ---
    def bad_score_call_fn(system_prompt: str, user_prompt: str) -> str:
        return '{"relevant": true, "score": 7.5, "reason": "Model ignored the 0-1 range."}'

    clamp_grader = DocumentGrader(call_fn=bad_score_call_fn)
    print("\n--- score clamping ---")
    print(clamp_grader.grade_one("q", {"id": 3, "payload": {"text": "some text"}}))

    # --- Retry + on_ungraded fallback: call_fn always raises ---
    def flaky_call_fn(system_prompt: str, user_prompt: str) -> str:
        raise ConnectionError("simulated transient API failure")

    flaky_grader = DocumentGrader(
        call_fn=flaky_call_fn, max_retries=1, retry_backoff_seconds=0.01, on_ungraded="not_relevant"
    )
    print("\n--- retry exhaustion / on_ungraded fallback ---")
    print(flaky_grader.grade_one("q", {"id": 4, "payload": {"text": "some text"}}))