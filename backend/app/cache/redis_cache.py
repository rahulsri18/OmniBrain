"""
redis_cache.py

Establishes and manages a single Redis connection for the application.

Scope of this module (intentionally limited):
    - Read Redis configuration from environment variables
    - Create and verify a Redis client connection
    - Expose the client instance for use elsewhere
    - Handle connection failures with logging/exceptions

Out of scope for this commit (to be added later):
    - get() / set() / delete() / clear()
    - Integration with hybrid_search.py
    - Caching of retrieval results
"""

import os
import logging

import redis

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Manages the lifecycle of a single Redis connection.

    Configuration is read from environment variables:
        REDIS_HOST     - Redis server host (default: "localhost")
        REDIS_PORT     - Redis server port (default: 6379)
        REDIS_DB       - Redis logical database index (default: 0)
        REDIS_PASSWORD - Redis password, if required (default: None)
    """

    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        self.password = os.getenv("REDIS_PASSWORD") or None

        self._client = None
        self._connect()

    def _connect(self):
        """
        Create the Redis client and verify the connection with a ping.

        Raises:
            redis.exceptions.RedisError: if the connection cannot be
            established or the ping check fails.
        """
        try:
            client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
            )
            # Verify the connection is actually usable, not just constructed.
            client.ping()

            self._client = client
            logger.info(
                "Connected to Redis at %s:%s (db=%s)",
                self.host, self.port, self.db,
            )
        except redis.exceptions.RedisError as exc:
            logger.error(
                "Failed to connect to Redis at %s:%s (db=%s): %s",
                self.host, self.port, self.db, exc,
            )
            raise

    def get_client(self):
        """
        Return the active Redis client instance.

        Returns:
            redis.Redis: the connected client.

        Raises:
            RuntimeError: if called before a successful connection was made.
        """
        if self._client is None:
            raise RuntimeError("Redis client is not connected.")
        return self._client

    def close(self):
        """Close the underlying Redis connection, if open."""
        if self._client is not None:
            try:
                self._client.close()
                logger.info("Redis connection closed.")
            except redis.exceptions.RedisError as exc:
                logger.warning("Error while closing Redis connection: %s", exc)
            finally:
                self._client = None


if __name__ == "__main__":
    # Smoke test: run this file directly to verify connectivity.
    logging.basicConfig(level=logging.INFO)
    cache = RedisCache()
    print(cache.get_client())
    cache.close()