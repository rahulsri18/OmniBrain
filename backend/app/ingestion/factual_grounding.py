import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
 
 
# Bump when GROUNDING_SYSTEM_PROMPT's wording changes meaningfully, same
# convention as GRADER_PROMPT_VERSION / TRANSFORMER_PROMPT_VERSION.
GROUNDING_PROMPT_VERSION = "v1.0"
 
DEFAULT_GROUNDING_MODEL = "claude-sonnet-4-6"
 
GROUNDING_SYSTEM_PROMPT = """You are a factual grounding verifier for a retrieval-augmented \
generation (RAG) system.
 
Your ONLY job is to check whether a generated answer is supported by the \
retrieved document context it was given. You do NOT answer the user's \
question yourself. You do NOT use outside knowledge -- judge the answer \
ONLY against the retrieved context provided to you, even if you know the \
claim to be true or false from general knowledge.
 
For each distinct factual claim in the answer, classify it as one of:
- "supported": the retrieved context contains information that backs up this claim.
- "unsupported": the retrieved context has no information addressing this claim \
(treat missing evidence as unsupported, not as supported).
- "contradicted": the retrieved context directly conflicts with this claim.
 
Then produce an overall judgment:
- "grounded" is true only if all claims are supported (no unsupported or \
contradicted claims).
- "grounding_score" is a float from 0.0 to 1.0 representing the proportion \
of claims that are supported.
 
Respond with ONLY a JSON object in this exact format, and nothing else:
 
{
  "grounded": true or false,
  "grounding_score": <float between 0.0 and 1.0>,
  "supported_claims": ["<claim text>", ...],
  "unsupported_claims": ["<claim text>", ...],
  "contradicted_claims": ["<claim text>", ...],
  "explanation": "<one or two sentence summary of the verification>"
}
 
Do not include markdown code fences, preamble, or any text outside the JSON object.
If the answer contains no verifiable factual claims (e.g. it's a clarifying \
question or a refusal), return grounded=true, grounding_score=1.0, and empty \
claim lists, with an explanation noting there were no claims to verify.
"""
 
GROUNDING_USER_TEMPLATE = """Generated Answer:
{answer}
 
Retrieved Context:
{context}
"""
 
NO_CONTEXT_PLACEHOLDER = "(no context was retrieved)"

@dataclass
class GroundingResult:
    grounded: bool
    grounding_score: float
    supported_claims: List[str] = field(default_factory=list)
    unsupported_claims: List[str] = field(default_factory=list)
    contradicted_claims: List[str] = field(default_factory=list)
    explanation: str = ""
    ungraded: bool = False  # True if verification failed after retries (transient error)
    prompt_version: str = GROUNDING_PROMPT_VERSION
 
 
class GroundingVerifier:
    """
    Wraps an LLM client to verify that a generated answer is grounded in
    retrieved context.
 
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
        request_timeout: Optional[float] = 15.0,
        grounded_score_threshold: float = 0.7,
        on_ungraded: str = "not_grounded",  # "not_grounded" | "grounded" | "raise"
    ):
        if llm_client is None and call_fn is None:
            raise ValueError("Provide either llm_client or call_fn")
        if on_ungraded not in ("not_grounded", "grounded", "raise"):
            raise ValueError("on_ungraded must be 'not_grounded', 'grounded', or 'raise'")
 
        self.llm_client = llm_client
        self.model = model or os.environ.get("GROUNDING_MODEL", DEFAULT_GROUNDING_MODEL)
        self.call_fn = call_fn
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self.request_timeout = request_timeout
        self.grounded_score_threshold = grounded_score_threshold
        self.on_ungraded = on_ungraded

         # --- context handling -------------------------------------------------
 
    @staticmethod
    def _flatten_context(context_chunks: Any) -> str:
        """
        Accepts context as a single string, or a list of chunk dicts/strings
        (e.g. the same shape hybrid_search.py / document_grader.py produce),
        and flattens it into plain text for the prompt.
        """
        if context_chunks is None:
            return NO_CONTEXT_PLACEHOLDER
 
        if isinstance(context_chunks, str):
            return context_chunks.strip() or NO_CONTEXT_PLACEHOLDER
 
        if isinstance(context_chunks, list):
            parts = []
            for i, chunk in enumerate(context_chunks, start=1):
                if isinstance(chunk, str):
                    text = chunk
                elif isinstance(chunk, dict):
                    payload = chunk.get("payload") or {}
                    text = (
                        payload.get("text")
                        or payload.get("content")
                        or payload.get("chunk")
                        or chunk.get("text")
                        or ""
                    )
                else:
                    text = str(chunk)
                text = text.strip()
                if text:
                    parts.append(f"[Chunk {i}]\n{text}")
            return "\n\n".join(parts) if parts else NO_CONTEXT_PLACEHOLDER
 
        return str(context_chunks).strip() or NO_CONTEXT_PLACEHOLDER