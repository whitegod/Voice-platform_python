"""
Analytics Service
Captures metrics and usage data
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge
from ..data_layer.postgres import PostgresClient

logger = logging.getLogger(__name__)


# Prometheus metrics
REQUEST_COUNTER = Counter(
    'vaas_requests_total',
    'Total number of requests',
    ['tenant_id', 'domain', 'intent']
)

RESPONSE_TIME = Histogram(
    'vaas_response_duration_seconds',
    'Response duration in seconds',
    ['tenant_id', 'domain']
)

ACTIVE_SESSIONS = Gauge(
    'vaas_active_sessions',
    'Number of active sessions',
    ['tenant_id']
)

ERROR_COUNTER = Counter(
    'vaas_errors_total',
    'Total number of errors',
    ['tenant_id', 'error_type']
)


class AnalyticsService:
    """
    Captures and logs analytics events.
    Provides metrics for monitoring and business intelligence.
    """

    def __init__(self, postgres_client: PostgresClient, enabled: bool = True):
        """
        Initialize analytics service.

        Args:
            postgres_client: PostgreSQL client for event storage
            enabled: Whether analytics is enabled
        """
        self.db = postgres_client
        self.enabled = enabled
        logger.info(f"AnalyticsService initialized (enabled: {enabled})")

    async def log_request(
        self,
        tenant_id: str,
        domain: str,
        intent: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Log a request event.

        Args:
            tenant_id: Tenant identifier
            domain: Domain name
            intent: Detected intent
            user_id: User identifier
            session_id: Session identifier
            metadata: Additional event data
        """
        if not self.enabled:
            return

        try:
            # Update Prometheus metrics
            REQUEST_COUNTER.labels(
                tenant_id=tenant_id,
                domain=domain,
                intent=intent or 'unknown'
            ).inc()

            # Log to database
            event_data = {
                "domain": domain,
                "intent": intent,
                "user_id": user_id,
                "session_id": session_id,
                **(metadata or {})
            }

            await self.db.log_event(
                tenant_id=tenant_id,
                event_type="request",
                event_data=event_data
            )

            logger.debug(f"Logged request event for tenant: {tenant_id}")

        except Exception as e:
            logger.error(f"Failed to log request: {e}")

    async def log_response(
        self,
        tenant_id: str,
        domain: str,
        response_time: float,
        success: bool,
        metadata: Optional[Dict] = None
    ):
        """
        Log a response event.

        Args:
            tenant_id: Tenant identifier
            domain: Domain name
            response_time: Response time in seconds
            success: Whether request was successful
            metadata: Additional event data
        """
        if not self.enabled:
            return

        try:
            # Update Prometheus metrics
            RESPONSE_TIME.labels(
                tenant_id=tenant_id,
                domain=domain
            ).observe(response_time)

            # Log to database
            event_data = {
                "domain": domain,
                "response_time": response_time,
                "success": success,
                **(metadata or {})
            }

            await self.db.log_event(
                tenant_id=tenant_id,
                event_type="response",
                event_data=event_data
            )

        except Exception as e:
            logger.error(f"Failed to log response: {e}")

    async def log_error(
        self,
        tenant_id: str,
        error_type: str,
        error_message: str,
        context: Optional[Dict] = None
    ):
        """
        Log an error event.

        Args:
            tenant_id: Tenant identifier
            error_type: Type of error
            error_message: Error message
            context: Error context
        """
        if not self.enabled:
            return

        try:
            # Update Prometheus metrics
            ERROR_COUNTER.labels(
                tenant_id=tenant_id,
                error_type=error_type
            ).inc()

            # Log to database
            event_data = {
                "error_type": error_type,
                "error_message": error_message,
                "context": context or {}
            }

            await self.db.log_event(
                tenant_id=tenant_id,
                event_type="error",
                event_data=event_data
            )

            logger.debug(f"Logged error event: {error_type}")

        except Exception as e:
            logger.error(f"Failed to log error: {e}")

    async def log_moderation(
        self,
        tenant_id: str,
        is_safe: bool,
        flagged_categories: list,
        metadata: Optional[Dict] = None
    ):
        """
        Log content moderation event.

        Args:
            tenant_id: Tenant identifier
            is_safe: Whether content passed moderation
            flagged_categories: Categories flagged
            metadata: Additional data
        """
        if not self.enabled:
            return

        try:
            event_data = {
                "is_safe": is_safe,
                "flagged_categories": flagged_categories,
                **(metadata or {})
            }

            await self.db.log_event(
                tenant_id=tenant_id,
                event_type="moderation",
                event_data=event_data
            )

        except Exception as e:
            logger.error(f"Failed to log moderation: {e}")

    async def log_api_call(
        self,
        tenant_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        metadata: Optional[Dict] = None
    ):
        """
        Log external API call.

        Args:
            tenant_id: Tenant identifier
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status
            response_time: Response time
            metadata: Additional data
        """
        if not self.enabled:
            return

        try:
            event_data = {
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "response_time": response_time,
                **(metadata or {})
            }

            await self.db.log_event(
                tenant_id=tenant_id,
                event_type="api_call",
                event_data=event_data
            )

        except Exception as e:
            logger.error(f"Failed to log API call: {e}")

    def update_active_sessions(self, tenant_id: str, count: int):
        """
        Update active session gauge.

        Args:
            tenant_id: Tenant identifier
            count: Number of active sessions
        """
        if not self.enabled:
            return

        try:
            ACTIVE_SESSIONS.labels(tenant_id=tenant_id).set(count)
        except Exception as e:
            logger.error(f"Failed to update active sessions: {e}")

    async def get_metrics(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get analytics metrics for tenant.

        Args:
            tenant_id: Tenant identifier
            start_date: Start date for metrics
            end_date: End date for metrics

        Returns:
            Metrics dictionary
        """
        try:
            # This would query the analytics table with date filters
            # Placeholder implementation
            return {
                "tenant_id": tenant_id,
                "total_requests": 0,
                "total_errors": 0,
                "avg_response_time": 0.0,
                "success_rate": 0.0
            }

        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {}

