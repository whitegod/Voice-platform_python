"""
Redis Client for Session Management and Caching
Fast key-value store for conversational context
"""

import logging
import json
from typing import Optional, Any, Dict
import redis.asyncio as redis
from datetime import timedelta

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis client for managing user sessions and caching.
    Stores conversational context with TTL.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        default_ttl: int = 3600
    ):
        """
        Initialize Redis client.

        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number
            password: Redis password (if any)
            default_ttl: Default TTL for keys in seconds
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.default_ttl = default_ttl
        self.client = None
        
        logger.info(f"Initializing Redis client: {host}:{port}/{db}")

    async def connect(self):
        """Establish connection to Redis"""
        try:
            self.client = await redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True
            )
            
            # Test connection
            await self.client.ping()
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: str = "vaas"
    ) -> bool:
        """
        Set a key-value pair.

        Args:
            key: Key name
            value: Value (will be JSON serialized)
            ttl: Time to live in seconds
            namespace: Key namespace prefix

        Returns:
            True if successful
        """
        try:
            full_key = f"{namespace}:{key}"
            
            # Serialize value
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            ttl = ttl or self.default_ttl
            
            await self.client.set(full_key, value, ex=ttl)
            logger.debug(f"Set key: {full_key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set key {key}: {e}")
            return False

    async def get(
        self,
        key: str,
        namespace: str = "vaas",
        deserialize: bool = True
    ) -> Optional[Any]:
        """
        Get value by key.

        Args:
            key: Key name
            namespace: Key namespace prefix
            deserialize: Whether to deserialize JSON

        Returns:
            Value or None if not found
        """
        try:
            full_key = f"{namespace}:{key}"
            value = await self.client.get(full_key)
            
            if value is None:
                return None
            
            # Deserialize if needed
            if deserialize:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            
            return value
            
        except Exception as e:
            logger.error(f"Failed to get key {key}: {e}")
            return None

    async def delete(self, key: str, namespace: str = "vaas") -> bool:
        """
        Delete a key.

        Args:
            key: Key name
            namespace: Key namespace prefix

        Returns:
            True if successful
        """
        try:
            full_key = f"{namespace}:{key}"
            await self.client.delete(full_key)
            logger.debug(f"Deleted key: {full_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete key {key}: {e}")
            return False

    async def exists(self, key: str, namespace: str = "vaas") -> bool:
        """Check if key exists"""
        try:
            full_key = f"{namespace}:{key}"
            result = await self.client.exists(full_key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to check key existence {key}: {e}")
            return False

    async def expire(self, key: str, ttl: int, namespace: str = "vaas") -> bool:
        """Set expiration time for a key"""
        try:
            full_key = f"{namespace}:{key}"
            await self.client.expire(full_key, ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to set expiration for key {key}: {e}")
            return False

    # Session-specific methods
    async def save_session(
        self,
        session_id: str,
        session_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Save user session data"""
        return await self.set(
            f"session:{session_id}",
            session_data,
            ttl=ttl,
            namespace="vaas"
        )

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user session data"""
        return await self.get(f"session:{session_id}", namespace="vaas")

    async def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update session data"""
        try:
            session = await self.get_session(session_id)
            if session is None:
                session = {}
            
            session.update(updates)
            return await self.save_session(session_id, session)
            
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return False

    async def delete_session(self, session_id: str) -> bool:
        """Delete user session"""
        return await self.delete(f"session:{session_id}", namespace="vaas")

    # Cache methods
    async def cache_set(
        self,
        cache_key: str,
        data: Any,
        ttl: int = 300
    ) -> bool:
        """Cache data with short TTL"""
        return await self.set(
            f"cache:{cache_key}",
            data,
            ttl=ttl,
            namespace="vaas"
        )

    async def cache_get(self, cache_key: str) -> Optional[Any]:
        """Get cached data"""
        return await self.get(f"cache:{cache_key}", namespace="vaas")

    async def health_check(self) -> bool:
        """Check Redis health"""
        try:
            await self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

