"""
PostgreSQL Client for System Configuration and Multi-Tenant Data
Primary database for persistent storage
"""

import logging
import os
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import asyncpg
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class PostgresClient:
    """
    PostgreSQL client for managing system configuration and tenant data.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "vaas_platform",
        user: str = "vaas_user",
        password: str = "",
        min_pool_size: Optional[int] = None,
        max_pool_size: Optional[int] = None
    ):
        """
        Initialize PostgreSQL client.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            min_pool_size: Minimum connection pool size
            max_pool_size: Maximum connection pool size
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.min_pool_size = min_pool_size if min_pool_size is not None else int(os.getenv("POSTGRES_MIN_POOL_SIZE", "5"))
        self.max_pool_size = max_pool_size if max_pool_size is not None else int(os.getenv("POSTGRES_MAX_POOL_SIZE", "20"))
        self.pool = None
        
        logger.info(f"Initializing Postgres client: {host}:{port}/{database}")

    async def connect(self):
        """Create connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=self.min_pool_size,
                max_size=self.max_pool_size
            )
            
            logger.info("PostgreSQL connection pool created successfully")
            
            # Initialize schema
            await self.initialize_schema()
            
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")

    async def initialize_schema(self):
        """Create necessary database tables"""
        try:
            async with self.pool.acquire() as conn:
                # Tenants table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS tenants (
                        id SERIAL PRIMARY KEY,
                        tenant_id VARCHAR(100) UNIQUE NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        api_key VARCHAR(255) UNIQUE NOT NULL,
                        is_active BOOLEAN DEFAULT true,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                ''')

                # Domains table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS domains (
                        id SERIAL PRIMARY KEY,
                        tenant_id VARCHAR(100) REFERENCES tenants(tenant_id),
                        domain_name VARCHAR(100) NOT NULL,
                        config JSONB NOT NULL,
                        is_active BOOLEAN DEFAULT true,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),
                        UNIQUE(tenant_id, domain_name)
                    )
                ''')

                # Conversations table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS conversations (
                        id SERIAL PRIMARY KEY,
                        conversation_id VARCHAR(100) UNIQUE NOT NULL,
                        tenant_id VARCHAR(100) REFERENCES tenants(tenant_id),
                        user_id VARCHAR(100) NOT NULL,
                        domain_name VARCHAR(100),
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                ''')

                # Messages table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS messages (
                        id SERIAL PRIMARY KEY,
                        message_id VARCHAR(100) UNIQUE NOT NULL,
                        conversation_id VARCHAR(100) REFERENCES conversations(conversation_id),
                        role VARCHAR(50) NOT NULL,
                        content TEXT NOT NULL,
                        intent VARCHAR(100),
                        entities JSONB,
                        moderation_result JSONB,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                ''')

                # Analytics table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS analytics (
                        id SERIAL PRIMARY KEY,
                        tenant_id VARCHAR(100),
                        event_type VARCHAR(100) NOT NULL,
                        event_data JSONB,
                        timestamp TIMESTAMP DEFAULT NOW()
                    )
                ''')

                # Create indices
                await conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_conversations_tenant 
                    ON conversations(tenant_id)
                ''')
                await conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_messages_conversation 
                    ON messages(conversation_id)
                ''')
                await conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_analytics_tenant 
                    ON analytics(tenant_id, timestamp)
                ''')

                logger.info("Database schema initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise

    # Tenant operations
    async def create_tenant(
        self,
        tenant_id: str,
        name: str,
        api_key: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Create a new tenant"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    '''
                    INSERT INTO tenants (tenant_id, name, api_key, metadata)
                    VALUES ($1, $2, $3, $4)
                    ''',
                    tenant_id, name, api_key, json.dumps(metadata or {})
                )
                logger.info(f"Created tenant: {tenant_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create tenant: {e}")
            return False

    async def get_tenant(self, tenant_id: str) -> Optional[Dict]:
        """Get tenant by ID"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    'SELECT * FROM tenants WHERE tenant_id = $1',
                    tenant_id
                )
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Failed to get tenant: {e}")
            return None

    async def verify_api_key(self, api_key: str) -> Optional[str]:
        """Verify API key and return tenant_id"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    'SELECT tenant_id FROM tenants WHERE api_key = $1 AND is_active = true',
                    api_key
                )
                return row['tenant_id'] if row else None
                
        except Exception as e:
            logger.error(f"Failed to verify API key: {e}")
            return None

    # Domain operations
    async def save_domain_config(
        self,
        tenant_id: str,
        domain_name: str,
        config: Dict
    ) -> bool:
        """Save or update domain configuration"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    '''
                    INSERT INTO domains (tenant_id, domain_name, config)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (tenant_id, domain_name) 
                    DO UPDATE SET config = $3, updated_at = NOW()
                    ''',
                    tenant_id, domain_name, json.dumps(config)
                )
                logger.info(f"Saved domain config: {tenant_id}/{domain_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save domain config: {e}")
            return False

    async def get_domain_config(
        self,
        tenant_id: str,
        domain_name: str
    ) -> Optional[Dict]:
        """Get domain configuration"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    '''
                    SELECT config FROM domains 
                    WHERE tenant_id = $1 AND domain_name = $2 AND is_active = true
                    ''',
                    tenant_id, domain_name
                )
                return row['config'] if row else None
                
        except Exception as e:
            logger.error(f"Failed to get domain config: {e}")
            return None

    # Conversation operations
    async def create_conversation(
        self,
        conversation_id: str,
        tenant_id: str,
        user_id: str,
        domain_name: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Create a new conversation"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    '''
                    INSERT INTO conversations 
                    (conversation_id, tenant_id, user_id, domain_name, metadata)
                    VALUES ($1, $2, $3, $4, $5)
                    ''',
                    conversation_id, tenant_id, user_id, domain_name,
                    json.dumps(metadata or {})
                )
                return True
                
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            return False

    async def save_message(
        self,
        message_id: str,
        conversation_id: str,
        role: str,
        content: str,
        intent: Optional[str] = None,
        entities: Optional[Dict] = None,
        moderation_result: Optional[Dict] = None
    ) -> bool:
        """Save a message"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    '''
                    INSERT INTO messages 
                    (message_id, conversation_id, role, content, intent, entities, moderation_result)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ''',
                    message_id, conversation_id, role, content, intent,
                    json.dumps(entities or {}), json.dumps(moderation_result or {})
                )
                return True
                
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            return False

    # Analytics operations
    async def log_event(
        self,
        tenant_id: str,
        event_type: str,
        event_data: Dict
    ) -> bool:
        """Log an analytics event"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    '''
                    INSERT INTO analytics (tenant_id, event_type, event_data)
                    VALUES ($1, $2, $3)
                    ''',
                    tenant_id, event_type, json.dumps(event_data)
                )
                return True
                
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
            return False

    async def health_check(self) -> bool:
        """Check database health"""
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval('SELECT 1')
                return True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return False

