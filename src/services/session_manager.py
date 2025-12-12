"""
Session Manager
Manages user conversation sessions and context
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
from ..data_layer.redis_client import RedisClient

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages user conversation sessions with Redis backend.
    Maintains conversational context and history.
    """

    def __init__(self, redis_client: RedisClient, default_ttl: int = 3600):
        """
        Initialize session manager.

        Args:
            redis_client: Redis client instance
            default_ttl: Default session TTL in seconds
        """
        self.redis = redis_client
        self.default_ttl = default_ttl
        logger.info("SessionManager initialized")

    async def create_session(
        self,
        user_id: str,
        tenant_id: str,
        domain: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create a new session.

        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            domain: Domain name
            metadata: Additional metadata

        Returns:
            Session ID
        """
        try:
            session_id = str(uuid.uuid4())
            
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "tenant_id": tenant_id,
                "domain": domain,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "message_count": 0,
                "context": {},
                "history": [],
                "metadata": metadata or {}
            }

            await self.redis.save_session(
                session_id,
                session_data,
                ttl=self.default_ttl
            )

            logger.info(f"Created session: {session_id} for user {user_id}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data.

        Args:
            session_id: Session identifier

        Returns:
            Session data or None
        """
        try:
            session = await self.redis.get_session(session_id)
            
            if session:
                logger.debug(f"Retrieved session: {session_id}")
            else:
                logger.warning(f"Session not found: {session_id}")
            
            return session

        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None

    async def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update session data.

        Args:
            session_id: Session identifier
            updates: Updates to apply

        Returns:
            True if successful
        """
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            success = await self.redis.update_session(session_id, updates)
            
            if success:
                logger.debug(f"Updated session: {session_id}")
            
            return success

        except Exception as e:
            logger.error(f"Failed to update session: {e}")
            return False

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        intent: Optional[str] = None,
        entities: Optional[Dict] = None
    ) -> bool:
        """
        Add a message to session history.

        Args:
            session_id: Session identifier
            role: Message role (user/assistant)
            content: Message content
            intent: Detected intent
            entities: Extracted entities

        Returns:
            True if successful
        """
        try:
            session = await self.get_session(session_id)
            if not session:
                logger.error(f"Cannot add message - session not found: {session_id}")
                return False

            message = {
                "role": role,
                "content": content,
                "intent": intent,
                "entities": entities or {},
                "timestamp": datetime.utcnow().isoformat()
            }

            history = session.get("history", [])
            history.append(message)

            # Keep last 50 messages
            if len(history) > 50:
                history = history[-50:]

            await self.update_session(session_id, {
                "history": history,
                "message_count": session.get("message_count", 0) + 1
            })

            logger.debug(f"Added message to session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            return False

    async def get_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history.

        Args:
            session_id: Session identifier
            limit: Maximum messages to return

        Returns:
            List of messages
        """
        try:
            session = await self.get_session(session_id)
            if not session:
                return []

            history = session.get("history", [])
            
            if limit:
                history = history[-limit:]

            return history

        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return []

    async def update_context(
        self,
        session_id: str,
        context_updates: Dict[str, Any]
    ) -> bool:
        """
        Update session context (slots, variables).

        Args:
            session_id: Session identifier
            context_updates: Context updates

        Returns:
            True if successful
        """
        try:
            session = await self.get_session(session_id)
            if not session:
                return False

            context = session.get("context", {})
            context.update(context_updates)

            return await self.update_session(session_id, {"context": context})

        except Exception as e:
            logger.error(f"Failed to update context: {e}")
            return False

    async def get_context(self, session_id: str) -> Dict[str, Any]:
        """Get session context"""
        try:
            session = await self.get_session(session_id)
            return session.get("context", {}) if session else {}

        except Exception as e:
            logger.error(f"Failed to get context: {e}")
            return {}

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        try:
            success = await self.redis.delete_session(session_id)
            
            if success:
                logger.info(f"Deleted session: {session_id}")
            
            return success

        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False

    async def extend_session(self, session_id: str, ttl: Optional[int] = None) -> bool:
        """
        Extend session expiration.

        Args:
            session_id: Session identifier
            ttl: New TTL in seconds

        Returns:
            True if successful
        """
        try:
            ttl = ttl or self.default_ttl
            return await self.redis.expire(
                f"session:{session_id}",
                ttl,
                namespace="vaas"
            )

        except Exception as e:
            logger.error(f"Failed to extend session: {e}")
            return False

    async def get_active_sessions(self, user_id: str) -> List[str]:
        """
        Get all active sessions for a user (placeholder).

        Args:
            user_id: User identifier

        Returns:
            List of session IDs
        """
        # Note: This would require a Redis index or scan operation
        # For production, maintain a user->sessions mapping
        logger.warning("get_active_sessions not fully implemented")
        return []

