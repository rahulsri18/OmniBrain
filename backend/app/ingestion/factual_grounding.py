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