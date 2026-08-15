"""
session_manager.py

Session-ID & Chat History Manager for OmniBrain.
Supports both In-Memory storage (for fast local dev) and Redis (for scalable production).
"""

import uuid
import os
import time
from typing import Dict, List, Optional, Any
from app.logger import logger

# Optional Redis Import (Fallback to In-Memory if redis package is missing or unconfigured)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class SessionManager:
    def __init__(self, ttl_seconds: int = 86400):
        self.ttl_seconds = ttl_seconds
        self.redis_url = os.getenv("REDIS_URL", None)
        self.use_redis = REDIS_AVAILABLE and bool(self.redis_url)

        if self.use_redis:
            try:
                self.redis_client = redis.Redis.from_url(self.redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info("Connected to Redis successfully for Session Management.")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis ({e}). Falling back to In-Memory session storage.")
                self.use_redis = False
                self._in_memory_store: Dict[str, Dict[str, Any]] = {}
        else:
            logger.info("Using In-Memory Session Manager.")
            self._in_memory_store: Dict[str, Dict[str, Any]] = {}

    def create_session(self, user_id: Optional[str] = None, metadata: Optional[dict] = None) -> str:
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        created_at = time.time()

        session_data = {
            "session_id": session_id,
            "user_id": user_id or "anonymous",
            "created_at": created_at,
            "updated_at": created_at,
            "metadata": metadata or {},
            "history": []
        }

        if self.use_redis:
            import json
            key = f"omnibrain:session:{session_id}"
            self.redis_client.setex(key, self.ttl_seconds, json.dumps(session_data))
        else:
            self._in_memory_store[session_id] = session_data

        logger.info(f"Created new session: {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        if self.use_redis:
            import json
            key = f"omnibrain:session:{session_id}"
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        else:
            return self._in_memory_store.get(session_id)

    def add_message(self, session_id: str, role: str, content: str) -> bool:
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"Attempted to add message to non-existent session: {session_id}")
            return False

        message_entry = {
            "role": role,
            "content": content,
            "timestamp": time.time()
        }

        session["history"].append(message_entry)
        session["updated_at"] = time.time()

        if self.use_redis:
            import json
            key = f"omnibrain:session:{session_id}"
            self.redis_client.setex(key, self.ttl_seconds, json.dumps(session))
        else:
            self._in_memory_store[session_id] = session

        return True

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        session = self.get_session(session_id)
        if session:
            return session.get("history", [])
        return []

    def clear_session(self, session_id: str) -> bool:
        if self.use_redis:
            key = f"omnibrain:session:{session_id}"
            result = self.redis_client.delete(key)
            return result > 0
        else:
            if session_id in self._in_memory_store:
                del self._in_memory_store[session_id]
                return True
            return False


# Global Singleton Instance for easy import across FastAPI / LangGraph
session_manager = SessionManager()