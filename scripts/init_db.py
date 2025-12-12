"""
Database Initialization Script
Sets up the database schema and creates sample tenant
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.data_layer import PostgresClient
from src.services import TenantManager

load_dotenv()


async def main():
    """Initialize database"""
    print("Initializing VaaS Platform Database...")
    
    try:
        # Connect to PostgreSQL
        postgres = PostgresClient(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "vaas_platform"),
            user=os.getenv("POSTGRES_USER", "vaas_user"),
            password=os.getenv("POSTGRES_PASSWORD", "")
        )
        
        print("Connecting to database...")
        await postgres.connect()
        
        print("✅ Database schema initialized!")
        
        # Create sample tenant
        tenant_manager = TenantManager(postgres)
        
        print("\nCreating sample tenant...")
        api_key = await tenant_manager.create_tenant(
            tenant_id="demo_tenant",
            name="Demo Tenant",
            email="demo@example.com",
            metadata={"tier": "free", "created_by": "init_script"}
        )
        
        if api_key:
            print(f"\n✅ Sample tenant created!")
            print(f"Tenant ID: demo_tenant")
            print(f"API Key: {api_key}")
            print(f"\nSave this API key - you'll need it to authenticate!")
        else:
            print("⚠️  Tenant may already exist")
        
        # Cleanup
        await postgres.disconnect()
        
        print("\n✅ Database initialization complete!")
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

