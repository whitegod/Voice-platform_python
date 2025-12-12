#!/usr/bin/env python3
"""
Environment Setup Script
Helps create and configure the .env file with API keys
"""

import os
from pathlib import Path
import secrets


def generate_secure_key(length: int = 32) -> str:
    """Generate a secure random key"""
    return secrets.token_urlsafe(length)


def create_env_file():
    """Create .env file with guided prompts"""
    print("=" * 70)
    print("Voice-as-a-Service Platform - Environment Setup")
    print("=" * 70)
    print()
    
    env_path = Path(".env")
    
    if env_path.exists():
        response = input(".env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return
    
    print("\nLet's set up your environment variables.")
    print("Press Enter to use default values shown in [brackets]\n")
    
    # Collect configuration
    config = {}
    
    # Basic Settings
    print("--- Basic Settings ---")
    config['APP_NAME'] = input("App Name [VoiceAsAService]: ") or "VoiceAsAService"
    config['ENVIRONMENT'] = input("Environment (development/production) [development]: ") or "development"
    config['DEBUG'] = input("Debug mode (true/false) [true]: ") or "true"
    config['LOG_LEVEL'] = input("Log Level (DEBUG/INFO/WARNING/ERROR) [INFO]: ") or "INFO"
    print()
    
    # API Gateway
    print("--- API Gateway ---")
    config['API_HOST'] = input("API Host [0.0.0.0]: ") or "0.0.0.0"
    config['API_PORT'] = input("API Port [8000]: ") or "8000"
    
    print("\nGenerating secure API secret key...")
    config['API_SECRET_KEY'] = generate_secure_key()
    print(f"Generated: {config['API_SECRET_KEY'][:20]}...")
    print()
    
    # OpenAI (Required)
    print("--- OpenAI Configuration (REQUIRED) ---")
    print("Get your API key from: https://platform.openai.com/api-keys")
    config['OPENAI_API_KEY'] = input("OpenAI API Key: ").strip()
    if not config['OPENAI_API_KEY']:
        print("⚠️  Warning: OpenAI API key is required for the platform to work!")
    config['OPENAI_MODEL'] = input("OpenAI Model [gpt-4-turbo-preview]: ") or "gpt-4-turbo-preview"
    print()
    
    # Optional LLM Providers
    print("--- Optional LLM Providers ---")
    use_anthropic = input("Add Anthropic Claude? (y/N): ").lower() == 'y'
    if use_anthropic:
        config['ANTHROPIC_API_KEY'] = input("Anthropic API Key: ").strip()
    else:
        config['ANTHROPIC_API_KEY'] = ""
    
    use_vertex = input("Add Google Vertex AI? (y/N): ").lower() == 'y'
    if use_vertex:
        config['GOOGLE_CLOUD_PROJECT'] = input("GCP Project ID: ").strip()
        config['GOOGLE_APPLICATION_CREDENTIALS'] = input("Service Account JSON path: ").strip()
    else:
        config['GOOGLE_CLOUD_PROJECT'] = ""
        config['GOOGLE_APPLICATION_CREDENTIALS'] = ""
    print()
    
    # Database Settings
    print("--- Database Configuration ---")
    config['POSTGRES_HOST'] = input("PostgreSQL Host [localhost]: ") or "localhost"
    config['POSTGRES_PORT'] = input("PostgreSQL Port [5432]: ") or "5432"
    config['POSTGRES_DB'] = input("Database Name [vaas_platform]: ") or "vaas_platform"
    config['POSTGRES_USER'] = input("Database User [vaas_user]: ") or "vaas_user"
    
    gen_pg_pass = input("Generate secure PostgreSQL password? (Y/n): ").lower() != 'n'
    if gen_pg_pass:
        config['POSTGRES_PASSWORD'] = generate_secure_key()
        print(f"Generated: {config['POSTGRES_PASSWORD'][:20]}...")
    else:
        config['POSTGRES_PASSWORD'] = input("PostgreSQL Password: ").strip()
    print()
    
    # Redis
    print("--- Redis Configuration ---")
    config['REDIS_HOST'] = input("Redis Host [localhost]: ") or "localhost"
    config['REDIS_PORT'] = input("Redis Port [6379]: ") or "6379"
    config['REDIS_DB'] = input("Redis DB [0]: ") or "0"
    config['REDIS_PASSWORD'] = input("Redis Password (leave empty if none): ").strip()
    print()
    
    # Qdrant
    print("--- Qdrant Vector DB Configuration ---")
    config['QDRANT_HOST'] = input("Qdrant Host [localhost]: ") or "localhost"
    config['QDRANT_PORT'] = input("Qdrant Port [6333]: ") or "6333"
    config['QDRANT_API_KEY'] = input("Qdrant API Key (leave empty if none): ").strip()
    print()
    
    # AI Models
    print("--- AI Model Configuration ---")
    print("Whisper Model sizes: tiny, base, small, medium, large")
    config['WHISPER_MODEL'] = input("Whisper Model [base]: ") or "base"
    config['WHISPER_DEVICE'] = input("Whisper Device (cpu/cuda) [cpu]: ") or "cpu"
    print()
    
    # Moderation
    print("--- Content Moderation ---")
    config['DETOXIFY_MODEL'] = input("Detoxify Model (original/unbiased/multilingual) [original]: ") or "original"
    config['MODERATION_THRESHOLD'] = input("Moderation Threshold (0.0-1.0) [0.7]: ") or "0.7"
    print()
    
    # Rate Limiting
    print("--- Rate Limiting ---")
    config['API_RATE_LIMIT_PER_MINUTE'] = input("Rate Limit per Minute [60]: ") or "60"
    config['API_RATE_LIMIT_PER_HOUR'] = input("Rate Limit per Hour [1000]: ") or "1000"
    print()
    
    # Write .env file
    print("\nCreating .env file...")
    
    env_content = f"""# Voice-as-a-Service Platform - Environment Configuration
# Generated by setup_env.py

# Application Settings
APP_NAME={config['APP_NAME']}
APP_VERSION=1.0.0
ENVIRONMENT={config['ENVIRONMENT']}
DEBUG={config['DEBUG']}
LOG_LEVEL={config['LOG_LEVEL']}

# API Gateway
API_HOST={config['API_HOST']}
API_PORT={config['API_PORT']}
API_SECRET_KEY={config['API_SECRET_KEY']}
API_ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM Providers
OPENAI_API_KEY={config['OPENAI_API_KEY']}
OPENAI_MODEL={config['OPENAI_MODEL']}
ANTHROPIC_API_KEY={config.get('ANTHROPIC_API_KEY', '')}
GOOGLE_CLOUD_PROJECT={config.get('GOOGLE_CLOUD_PROJECT', '')}
GOOGLE_APPLICATION_CREDENTIALS={config.get('GOOGLE_APPLICATION_CREDENTIALS', '')}
VERTEX_AI_LOCATION=us-central1
LOCAL_LLM_ENABLED=false
LOCAL_LLM_MODEL_PATH=models/llama-3-8b
LLM_PROVIDER=openai

# PostgreSQL
POSTGRES_HOST={config['POSTGRES_HOST']}
POSTGRES_PORT={config['POSTGRES_PORT']}
POSTGRES_DB={config['POSTGRES_DB']}
POSTGRES_USER={config['POSTGRES_USER']}
POSTGRES_PASSWORD={config['POSTGRES_PASSWORD']}
POSTGRES_MIN_POOL_SIZE=5
POSTGRES_MAX_POOL_SIZE=20

# Redis
REDIS_HOST={config['REDIS_HOST']}
REDIS_PORT={config['REDIS_PORT']}
REDIS_DB={config['REDIS_DB']}
REDIS_PASSWORD={config['REDIS_PASSWORD']}
REDIS_SESSION_TTL=3600

# Qdrant
QDRANT_HOST={config['QDRANT_HOST']}
QDRANT_PORT={config['QDRANT_PORT']}
QDRANT_API_KEY={config['QDRANT_API_KEY']}
QDRANT_COLLECTION_NAME=vaas_embeddings
QDRANT_VECTOR_SIZE=384

# Whisper ASR
WHISPER_MODEL={config['WHISPER_MODEL']}
WHISPER_DEVICE={config['WHISPER_DEVICE']}
WHISPER_LANGUAGE=en

# Coqui TTS
TTS_MODEL=tts_models/en/ljspeech/tacotron2-DDC
TTS_DEVICE=cpu

# Rasa NLU
RASA_ENDPOINT=http://localhost:5005
RASA_MODEL_PATH=models/rasa

# Content Moderation
DETOXIFY_MODEL={config['DETOXIFY_MODEL']}
MODERATION_THRESHOLD={config['MODERATION_THRESHOLD']}

# Domain Configuration
DEFAULT_DOMAIN=real_estate
DOMAIN_CONFIG_PATH=config/domains

# Analytics & Monitoring
ENABLE_ANALYTICS=true
PROMETHEUS_PORT=9090
GRAFANA_PASSWORD=admin

# Rate Limiting
API_RATE_LIMIT_PER_MINUTE={config['API_RATE_LIMIT_PER_MINUTE']}
API_RATE_LIMIT_PER_HOUR={config['API_RATE_LIMIT_PER_HOUR']}
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print("\n✅ .env file created successfully!")
    print("\n" + "=" * 70)
    print("IMPORTANT: Save these credentials securely!")
    print("=" * 70)
    print(f"\nAPI Secret Key: {config['API_SECRET_KEY']}")
    print(f"PostgreSQL Password: {config['POSTGRES_PASSWORD']}")
    
    if not config['OPENAI_API_KEY']:
        print("\n⚠️  WARNING: OpenAI API key is missing!")
        print("   Add it to .env before starting the platform:")
        print("   OPENAI_API_KEY=sk-your-key-here")
    
    print("\n" + "=" * 70)
    print("Next Steps:")
    print("=" * 70)
    print("1. Review and edit .env file if needed")
    print("2. Start services: docker-compose up -d")
    print("3. Initialize database: docker-compose exec vaas_app python scripts/init_db.py")
    print("4. Load sample data: docker-compose exec vaas_app python scripts/load_sample_data.py")
    print("5. Test API: curl http://localhost:8000/health")
    print()


if __name__ == "__main__":
    try:
        create_env_file()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

