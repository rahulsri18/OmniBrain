"""
redis_cache.py
 
Caches hybrid-search retrieval results keyed by query, so repeated identical
queries skip embedding generation + Qdrant search entirely. This module
caches RETRIEVAL RESULTS ONLY -- not embeddings, not LLM output, not
document-grader or grounding-verifier results. Those are separate caching
concerns for a future task, if ever needed.
 
Sits alongside document_grader.py, factual_grounding.py, and
query_transformer.py in spirit (same project conventions -- lazy client
init, env-var config, safe fallback on failure) but lives in its own
`cache/` package since it isn't retrieval logic itself.
 
Expected usage:
 
    from cache.redis_cache import RedisCache
 
    cache = RedisCache()
    cache.connect()
 
    cached = cache.get(query)
    if cached is not None:
        return cached
 
    results = hybrid_search(query)
    cache.set(query, results)
    return results
"""
 
import hashlib
import json
import os
from typing import Any, List, Optional
 
try:
    import redis
except ImportError:  # pragma: no cover - exercised only if redis isn't installed
    redis = None
 
 
DEFAULT_REDIS_HOST = "localhost"
DEFAULT_REDIS_PORT = 6379
DEFAULT_REDIS_DB = 0
DEFAULT_TTL_SECONDS = 300  # 5 minutes -- retrieval results go stale as documents are re-ingested
CACHE_KEY_PREFIX = "retrieval_cache"
 
 
class RedisCache:
    """
    Thin caching layer over Redis for retrieval results.
 
    Design choices:
    - Connection is lazy: connect() must be called explicitly (or is called
      automatically on first get/set/delete/clear if not yet connected),
      rather than opening a socket in __init__. This keeps constructing a
      RedisCache instance cheap and side-effect-free, which matters for
      testing and for app startup that shouldn't hard-fail if Redis isn't
      up yet.
    - All public methods fail SAFE, not loud: if Redis is unreachable, get()
      returns None (cache miss -- falls through to Qdrant), and set()/
      delete()/clear() silently no-op after logging. A cache outage should
      degrade retrieval to "slower", never "broken".
    - Keys are a hash of the normalized query text plus any extra
      parameters that affect results (top_k, page filters, etc.), so
      "What is RAG?" and "what is rag?" hit the same cache entry, but
      different top_k/filter combinations don't collide.
    """
 
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: Optional[int] = None,
        password: Optional[str] = None,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        key_prefix: str = CACHE_KEY_PREFIX,
        socket_timeout: float = 2.0,
        client: Any = None,
    ):
        if redis is None and client is None:
            raise ImportError(
                "redis-py is not installed. Run `pip install redis` or pass "
                "a pre-built client/fake client via the `client` argument "
                "(e.g. fakeredis, for tests)."
            )
 
        self.host = host or os.environ.get("REDIS_HOST", DEFAULT_REDIS_HOST)
        self.port = port or int(os.environ.get("REDIS_PORT", DEFAULT_REDIS_PORT))
        self.db = db if db is not None else int(os.environ.get("REDIS_DB", DEFAULT_REDIS_DB))
        self.password = password or os.environ.get("REDIS_PASSWORD") or None
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix
        self.socket_timeout = socket_timeout
 
        # Allows injecting a fakeredis client (or any redis-compatible
        # client) for tests without touching a real Redis instance.
        self._client = client
        self._connected = client is not None
 
    # --- connection management ---------------------------------------------
 
    def connect(self) -> bool:
        """
        Establish the Redis connection. Safe to call multiple times --
        no-ops if already connected. Returns True if connected (or already
        was), False if the connection attempt failed.
        """
        if self._connected and self._client is not None:
            return True
 
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_timeout,
                decode_responses=True,
            )
            self._client.ping()
            self._connected = True
            return True
        except Exception:
            # Connection failures are expected/recoverable (Redis down,
            # network blip) -- callers should keep working without cache
            # rather than crash. _connected stays False so the next
            # get/set call will retry connecting.
            self._client = None
            self._connected = False
            return False
 
    def _ensure_connected(self) -> bool:
        if self._connected and self._client is not None:
            return True
        return self.connect()
     # --- key construction ----------------------------------------------------
 
    def _make_key(self, query: str, **extra_params: Any) -> str:
        """
        Build a cache key from the normalized query plus any parameters
        that affect retrieval results (top_k, page filters, collection
        name, etc.), so different parameter combinations don't collide.
        """
        normalized_query = query.strip().lower()
        key_material = {"query": normalized_query, **extra_params}
        # Sort keys so parameter order never changes the resulting hash.
        serialized = json.dumps(key_material, sort_keys=True)
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return f"{self.key_prefix}:{digest}"