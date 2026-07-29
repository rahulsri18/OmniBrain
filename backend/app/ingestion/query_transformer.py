"""
query_transformer.py

Rewrites a user's query into clearer search-oriented terms when the initial
hybrid search doesn't return enough relevant results. Sits alongside
document_grader.py in the retrieval pipeline.

Expected usage:

    from query_transformer import QueryTransformer, enough_relevant

    transformer = QueryTransformer(llm_client=my_anthropic_client)

    results = retriever.search_text(query=user_query, top_k=10)
    graded = grader.grade_batch(user_query, results)

    if not enough_relevant(graded):
        rewritten = transformer.transform(user_query)
        results = retriever.search_text(query=rewritten, top_k=10)
        graded = grader.grade_batch(user_query, results)  # still grade against ORIGINAL intent
"""

import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


# Bump when TRANSFORMER_SYSTEM_PROMPT's wording changes meaningfully, same
# convention as GRADER_PROMPT_VERSION in document_grader.py.
TRANSFORMER_PROMPT_VERSION = "v1.0"

DEFAULT_TRANSFORMER_MODEL = "claude-sonnet-4-6"

TRANSFORMER_SYSTEM_PROMPT = """You are a search query rewriter for a retrieval-augmented \
generation (RAG) system.

Your ONLY job is to rewrite the user's query into terms that will retrieve \
better results from a hybrid (vector + keyword) search index. You do NOT \
answer the user's question. You do NOT add information the user didn't ask \
about.

When rewriting, you should:
- Expand abbreviations and acronyms where it's unambiguous to do so.
- Replace vague pronouns or references ("it", "that", "this thing") with the \
explicit entity or topic they refer to, using conversation context if given.
- Remove conversational filler ("can you tell me", "I was wondering", "please").
- Preserve the user's original intent and scope -- do not broaden or narrow \
the topic.
- Keep important named entities, technical terms, and domain vocabulary intact.
- Prefer concrete nouns and technical terms over full sentences or questions.

Respond with ONLY the rewritten query on a single line. No quotes, no \
preamble, no explanation, no markdown.
"""

TRANSFORMER_USER_TEMPLATE = """Original Query:
{query}
{context_block}"""

CONTEXT_BLOCK_TEMPLATE = """
Additional Context:
{context}
"""


@dataclass
class TransformResult:
    rewritten_query: str
    used_fallback: bool = False  # True if the LLM failed and we fell back to the original query


class QueryTransformer:
    """
    Wraps an LLM client to rewrite queries for better retrieval.

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
        max_retries: int = 2,
        retry_backoff_seconds: float = 1.0,
        request_timeout: Optional[float] = 10.0,
        max_query_length: int = 300,
    ):
        if llm_client is None and call_fn is None:
            raise ValueError("Provide either llm_client or call_fn")

        self.llm_client = llm_client
        self.model = model or os.environ.get("TRANSFORMER_MODEL", DEFAULT_TRANSFORMER_MODEL)
        self.call_fn = call_fn
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self.request_timeout = request_timeout
        self.max_query_length = max_query_length

    def _call_llm(self, query: str, context: Optional[str]) -> str:
        """Call the LLM with retries on transient failures. Raises on exhaustion."""
        context_block = CONTEXT_BLOCK_TEMPLATE.format(context=context) if context else ""
        user_prompt = TRANSFORMER_USER_TEMPLATE.format(query=query, context_block=context_block)

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                if self.call_fn is not None:
                    return self.call_fn(TRANSFORMER_SYSTEM_PROMPT, user_prompt)

                kwargs: Dict[str, Any] = dict(
                    model=self.model,
                    max_tokens=100,
                    system=TRANSFORMER_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                if self.request_timeout is not None:
                    kwargs["timeout"] = self.request_timeout

                response = self.llm_client.messages.create(**kwargs)
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
    def _clean_output(raw_text: str, max_length: int) -> str:
        """Strip quotes/fences/preamble the model might add despite instructions."""
        cleaned = raw_text.strip()
        cleaned = re.sub(r"^```\w*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
        cleaned = cleaned.strip().strip('"').strip("'")
        # If the model returned multiple lines anyway, take the first
        # non-empty one -- it's almost always the actual rewritten query.
        for line in cleaned.splitlines():
            line = line.strip()
            if line:
                cleaned = line
                break
        return cleaned[:max_length].strip()

    def transform(
        self,
        original_query: str,
        context: Optional[str] = None,
    ) -> TransformResult:
        """
        Rewrite a query for better retrieval.

        original_query: the user's raw query.
        context: optional extra signal -- e.g. previously retrieved chunks,
            the retrieval failure reason, or prior conversation turns, joined
            into a short string. Not required for basic use.
        """
        if not original_query or not original_query.strip():
            return TransformResult(rewritten_query=original_query, used_fallback=True)

        try:
            raw = self._call_llm(original_query, context)
            rewritten = self._clean_output(raw, self.max_query_length)
            if not rewritten:
                return TransformResult(rewritten_query=original_query, used_fallback=True)
            return TransformResult(rewritten_query=rewritten, used_fallback=False)
        except Exception:
            # Fail safe: if rewriting breaks, search with the original query
            # rather than blocking retrieval entirely.
            return TransformResult(rewritten_query=original_query, used_fallback=True)


def enough_relevant(graded_docs: List[Dict[str, Any]], min_relevant: int = 1) -> bool:
    """
    Decide whether graded retrieval results are sufficient, or a rewrite is needed.

    Expects docs shaped like document_grader.py's output, i.e. each dict has
    a "relevant" boolean key (as produced by DocumentGrader.grade_batch).
    """
    relevant_count = sum(1 for doc in graded_docs if doc.get("relevant"))
    return relevant_count >= min_relevant


if __name__ == "__main__":
    # --- Basic smoke test with a fake call_fn (no real API call) ---
    def fake_call_fn(system_prompt: str, user_prompt: str) -> str:
        if "transformers" in user_prompt.lower():
            return "transformer architecture deep learning attention mechanism"
        return "generic rewritten query"

    transformer = QueryTransformer(call_fn=fake_call_fn)

    print("--- basic rewrite ---")
    result = transformer.transform("What does it say about transformers?")
    print(result)

    # --- Model wraps output in quotes/fences despite instructions ---
    def messy_call_fn(system_prompt: str, user_prompt: str) -> str:
        return '```\n"transformer architecture attention mechanism"\n```'

    messy_transformer = QueryTransformer(call_fn=messy_call_fn)
    print("\n--- cleanup of messy model output ---")
    print(messy_transformer.transform("what does it say about transformers?"))

    # --- Retry exhaustion falls back to original query ---
    def flaky_call_fn(system_prompt: str, user_prompt: str) -> str:
        raise ConnectionError("simulated transient API failure")

    flaky_transformer = QueryTransformer(call_fn=flaky_call_fn, max_retries=1, retry_backoff_seconds=0.01)
    print("\n--- retry exhaustion / fallback to original query ---")
    print(flaky_transformer.transform("What does it say about transformers?"))

    # --- enough_relevant helper ---
    print("\n--- enough_relevant checks ---")
    print(enough_relevant([{"relevant": False}, {"relevant": False}]))  # False
    print(enough_relevant([{"relevant": False}, {"relevant": True}]))   # True
    print(enough_relevant([], min_relevant=1))                          # False