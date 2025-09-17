"""
Redis storage adapter for Rummikub game data.
Provides persistent storage with JSON serialization for game state.
"""

import redis
import json
import os
import threading
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class RedisStorage:
    """Redis-based storage adapter for game data."""
    
    def __init__(self):
        """Initialize Redis connection with environment-based configuration."""
        self.redis_host = os.environ.get("REDIS_HOST", "localhost")
        self.redis_port = int(os.environ.get("REDIS_PORT", "6379"))
        self.redis_db = int(os.environ.get("REDIS_DB", "0"))
        
        # Connection will be established when first needed
        self._redis = None
        self._connection_lock = threading.Lock()
        
    def _get_redis_connection(self) -> redis.Redis:
        """Get Redis connection, creating it if needed."""
        if self._redis is None:
            with self._connection_lock:
                if self._redis is None:  # Double-check after acquiring lock
                    try:
                        self._redis = redis.Redis(
                            host=self.redis_host,
                            port=self.redis_port,
                            db=self.redis_db,
                            decode_responses=True,
                            socket_connect_timeout=5,
                            socket_timeout=5,
                            retry_on_timeout=True
                        )
                        # Test connection
                        self._redis.ping()
                        logger.info(f"Connected to Redis at {self.redis_host}:{self.redis_port}")
                    except redis.ConnectionError as e:
                        logger.error(f"Failed to connect to Redis: {e}")
                        # Fall back to mock Redis for development
                        self._redis = MockRedis()
                        logger.warning("Using mock Redis storage (data will not persist)")
        return self._redis
    
    def set_json(self, key: str, value: Any) -> bool:
        """Store a JSON-serializable object in Redis."""
        try:
            redis_conn = self._get_redis_connection()
            serialized = json.dumps(value, default=self._json_serializer)
            return redis_conn.set(key, serialized)
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")
            return False
    
    def get_json(self, key: str) -> Optional[Any]:
        """Retrieve and deserialize a JSON object from Redis."""
        try:
            redis_conn = self._get_redis_connection()
            serialized = redis_conn.get(key)
            if serialized is None:
                return None
            return json.loads(serialized)
        except Exception as e:
            logger.error(f"Error getting key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        try:
            redis_conn = self._get_redis_connection()
            return bool(redis_conn.delete(key))
        except Exception as e:
            logger.error(f"Error deleting key {key}: {e}")
            return False
    
    def keys(self, pattern: str = "*") -> list:
        """Get all keys matching a pattern."""
        try:
            redis_conn = self._get_redis_connection()
            return redis_conn.keys(pattern)
        except Exception as e:
            logger.error(f"Error getting keys with pattern {pattern}: {e}")
            return []
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        try:
            redis_conn = self._get_redis_connection()
            return bool(redis_conn.exists(key))
        except Exception as e:
            logger.error(f"Error checking existence of key {key}: {e}")
            return False
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for special objects."""
        if hasattr(obj, 'model_dump'):  # Pydantic models
            return obj.model_dump()
        elif hasattr(obj, '__dict__'):  # Regular Python objects
            return obj.__dict__
        else:
            return str(obj)


class MockRedis:
    """Mock Redis implementation for development/testing when Redis is unavailable."""
    
    def __init__(self):
        self.data: Dict[str, str] = {}
        self.lock = threading.Lock()
    
    def set(self, key: str, value: str) -> bool:
        with self.lock:
            self.data[key] = value
            return True
    
    def get(self, key: str) -> Optional[str]:
        with self.lock:
            return self.data.get(key)
    
    def delete(self, key: str) -> int:
        with self.lock:
            if key in self.data:
                del self.data[key]
                return 1
            return 0
    
    def keys(self, pattern: str = "*") -> list:
        with self.lock:
            if pattern == "*":
                return list(self.data.keys())
            # Simple pattern matching for mock
            import fnmatch
            return [k for k in self.data.keys() if fnmatch.fnmatch(k, pattern)]
    
    def exists(self, key: str) -> int:
        with self.lock:
            return 1 if key in self.data else 0
    
    def ping(self) -> str:
        return "PONG"