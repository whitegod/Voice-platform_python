"""
Tenant Manager
Multi-tenant isolation and access control
"""

import logging
from typing import Optional, Dict, Any
import secrets
import hashlib
from ..data_layer.postgres import PostgresClient

logger = logging.getLogger(__name__)


class TenantManager:
    """
    Manages multi-tenant access control and isolation.
    Ensures data separation between tenants.
    """

    def __init__(self, postgres_client: PostgresClient):
        """
        Initialize tenant manager.

        Args:
            postgres_client: PostgreSQL client instance
        """
        self.db = postgres_client
        logger.info("TenantManager initialized")

    async def create_tenant(
        self,
        tenant_id: str,
        name: str,
        email: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Create a new tenant.

        Args:
            tenant_id: Unique tenant identifier
            name: Tenant name
            email: Contact email
            metadata: Additional metadata

        Returns:
            API key for the tenant or None if failed
        """
        try:
            # Generate secure API key
            api_key = self._generate_api_key(tenant_id)
            
            # Prepare metadata
            tenant_metadata = metadata or {}
            if email:
                tenant_metadata["email"] = email

            # Create tenant in database
            success = await self.db.create_tenant(
                tenant_id=tenant_id,
                name=name,
                api_key=api_key,
                metadata=tenant_metadata
            )

            if success:
                logger.info(f"Created tenant: {tenant_id}")
                return api_key
            else:
                logger.error(f"Failed to create tenant: {tenant_id}")
                return None

        except Exception as e:
            logger.error(f"Failed to create tenant: {e}")
            return None

    def _generate_api_key(self, tenant_id: str) -> str:
        """
        Generate secure API key for tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            API key string
        """
        # Generate random token
        random_part = secrets.token_urlsafe(32)
        
        # Create hash with tenant_id for uniqueness
        combined = f"{tenant_id}:{random_part}"
        hash_part = hashlib.sha256(combined.encode()).hexdigest()[:16]
        
        # Format: vaas_<tenant_id_prefix>_<hash>_<random>
        api_key = f"vaas_{tenant_id[:8]}_{hash_part}_{random_part}"
        
        return api_key

    async def verify_api_key(self, api_key: str) -> Optional[str]:
        """
        Verify API key and return tenant ID.

        Args:
            api_key: API key to verify

        Returns:
            Tenant ID if valid, None otherwise
        """
        try:
            tenant_id = await self.db.verify_api_key(api_key)
            
            if tenant_id:
                logger.debug(f"API key verified for tenant: {tenant_id}")
            else:
                logger.warning("Invalid API key provided")
            
            return tenant_id

        except Exception as e:
            logger.error(f"Failed to verify API key: {e}")
            return None

    async def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get tenant information.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Tenant data or None
        """
        try:
            tenant = await self.db.get_tenant(tenant_id)
            
            if tenant:
                # Don't expose API key in full
                if "api_key" in tenant:
                    tenant["api_key"] = self._mask_api_key(tenant["api_key"])
                
                logger.debug(f"Retrieved tenant: {tenant_id}")
            else:
                logger.warning(f"Tenant not found: {tenant_id}")
            
            return tenant

        except Exception as e:
            logger.error(f"Failed to get tenant: {e}")
            return None

    def _mask_api_key(self, api_key: str) -> str:
        """Mask API key for display"""
        if len(api_key) <= 12:
            return "***"
        return f"{api_key[:8]}...{api_key[-4:]}"

    async def update_tenant(
        self,
        tenant_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update tenant information.

        Args:
            tenant_id: Tenant identifier
            updates: Updates to apply

        Returns:
            True if successful
        """
        try:
            # This would need an update method in PostgresClient
            logger.warning("update_tenant not fully implemented")
            return False

        except Exception as e:
            logger.error(f"Failed to update tenant: {e}")
            return False

    async def deactivate_tenant(self, tenant_id: str) -> bool:
        """
        Deactivate a tenant (soft delete).

        Args:
            tenant_id: Tenant identifier

        Returns:
            True if successful
        """
        try:
            return await self.update_tenant(tenant_id, {"is_active": False})

        except Exception as e:
            logger.error(f"Failed to deactivate tenant: {e}")
            return False

    async def regenerate_api_key(self, tenant_id: str) -> Optional[str]:
        """
        Generate new API key for tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            New API key or None
        """
        try:
            new_api_key = self._generate_api_key(tenant_id)
            
            success = await self.update_tenant(
                tenant_id,
                {"api_key": new_api_key}
            )
            
            if success:
                logger.info(f"Regenerated API key for tenant: {tenant_id}")
                return new_api_key
            else:
                return None

        except Exception as e:
            logger.error(f"Failed to regenerate API key: {e}")
            return None

    async def check_permissions(
        self,
        tenant_id: str,
        resource: str,
        action: str
    ) -> bool:
        """
        Check if tenant has permission for action.

        Args:
            tenant_id: Tenant identifier
            resource: Resource name
            action: Action to perform

        Returns:
            True if permitted
        """
        try:
            # Basic implementation - can be extended with RBAC
            tenant = await self.get_tenant(tenant_id)
            
            if not tenant:
                return False
            
            # Check if tenant is active
            if not tenant.get("is_active", True):
                logger.warning(f"Tenant inactive: {tenant_id}")
                return False
            
            # Additional permission checks can be added here
            return True

        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return False

    async def get_tenant_usage(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get usage statistics for tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Usage statistics
        """
        try:
            # This would query analytics data
            # Placeholder implementation
            return {
                "tenant_id": tenant_id,
                "requests_today": 0,
                "requests_total": 0,
                "storage_used": 0
            }

        except Exception as e:
            logger.error(f"Failed to get tenant usage: {e}")
            return {}

