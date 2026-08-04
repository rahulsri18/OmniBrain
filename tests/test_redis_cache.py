"""
tests/test_redis_cache.py
"""

import pytest

try:
    import fakeredis
except ImportError:
    fakeredis = None

from backend.app.cache.redis_cache import RedisCache


@pytest.mark.skipif(fakeredis is None, reason="fakeredis not installed")
def test_redis_cache_get_set():
    """Verify basic set and get operations using fake redis."""
    fake_client = fakeredis.FakeStrictRedis(decode_responses=True)
    cache = RedisCache(client=fake_client)

    query = "What is Retrieval-Augmented Generation?"
    mock_results = [{"id": "doc_1", "score": 0.95, "payload": {"text": "RAG concept"}}]

    # Verify cache miss initially
    assert cache.get(query, top_k=5) is None

    # Set cache entry
    assert cache.set(query, mock_results, top_k=5) is True

    # Verify cache hit
    cached_data = cache.get(query, top_k=5)
    assert cached_data == mock_results

    # Verify key normalization (case and whitespace insensitivity)
    cached_data_normalized = cache.get("  what is retrieval-augmented generation?  ", top_k=5)
    assert cached_data_normalized == mock_results


@pytest.mark.skipif(fakeredis is None, reason="fakeredis not installed")
def test_redis_cache_clear():
    """Verify clear operation clears all matching keys under prefix."""
    fake_client = fakeredis.FakeStrictRedis(decode_responses=True)
    cache = RedisCache(client=fake_client)

    cache.set("query 1", [{"id": 1}])
    cache.set("query 2", [{"id": 2}])

    assert cache.get("query 1") is not None
    assert cache.get("query 2") is not None

    # Clear cache
    assert cache.clear() is True

    assert cache.get("query 1") is None
    assert cache.get("query 2") is None