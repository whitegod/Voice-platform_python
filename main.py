"""
Voice-as-a-Service Platform - Main Entry Point
"""

import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

from src.ai_core import WhisperASR, CoquiTTS, LLMProvider, RasaNLU, ContentModerator
from src.ai_core.llm import LLMProviderType
from src.data_layer import RedisClient, PostgresClient, QdrantVectorDB
from src.services import (
    PipelineOrchestrator,
    SessionManager,
    ConfigManager,
    TenantManager,
    AnalyticsService,
    DataAdapter,
    PolicyPlanner,
)
from src.services.api_gateway import APIGateway

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/vaas.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def initialize_services():
    """Initialize all VaaS services"""
    logger.info("Initializing Voice-as-a-Service Platform...")

    try:
        # Initialize AI Core
        logger.info("Loading AI core components...")
        
        asr = WhisperASR(
            model_name=os.getenv("WHISPER_MODEL", "base"),
            device=os.getenv("WHISPER_DEVICE", "cpu"),
            language=os.getenv("WHISPER_LANGUAGE", "en")
        )
        
        tts = CoquiTTS(
            model_name=os.getenv("TTS_MODEL", "tts_models/en/ljspeech/tacotron2-DDC"),
            device=os.getenv("TTS_DEVICE", "cpu")
        )
        
        # Determine LLM provider
        llm_provider_str = os.getenv("LLM_PROVIDER", "openai")
        llm_provider = LLMProviderType(llm_provider_str)
        
        llm = LLMProvider(
            provider=llm_provider,
            model_name=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
            temperature=0.7
        )
        
        nlu = RasaNLU(
            rasa_endpoint=os.getenv("RASA_ENDPOINT", "http://localhost:5005")
        )
        
        moderator = ContentModerator(
            model_name=os.getenv("DETOXIFY_MODEL", "original"),
            threshold=float(os.getenv("MODERATION_THRESHOLD", "0.7"))
        )

        # Initialize Data Layer
        logger.info("Connecting to data stores...")
        
        redis_client = RedisClient(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            password=os.getenv("REDIS_PASSWORD"),
            default_ttl=int(os.getenv("REDIS_SESSION_TTL", "3600"))
        )
        await redis_client.connect()
        
        postgres_client = PostgresClient(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "vaas_platform"),
            user=os.getenv("POSTGRES_USER", "vaas_user"),
            password=os.getenv("POSTGRES_PASSWORD", "")
        )
        await postgres_client.connect()
        
        qdrant_client = QdrantVectorDB(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
            api_key=os.getenv("QDRANT_API_KEY"),
            collection_name=os.getenv("QDRANT_COLLECTION_NAME", "vaas_embeddings"),
            vector_size=int(os.getenv("QDRANT_VECTOR_SIZE", "384"))
        )
        
        # Create default collection
        await qdrant_client.create_collection()

        # Initialize Services
        logger.info("Starting business logic services...")
        
        config_manager = ConfigManager(
            config_dir=os.getenv("DOMAIN_CONFIG_PATH", "config/domains")
        )
        config_manager.load_all_configs()
        
        session_manager = SessionManager(redis_client)
        tenant_manager = TenantManager(postgres_client)
        
        analytics = AnalyticsService(
            postgres_client,
            enabled=os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
        )
        
        data_adapter = DataAdapter(timeout=30, max_retries=3)
        
        policy_planner = PolicyPlanner(
            rate_limit_per_minute=int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "60")),
            rate_limit_per_hour=int(os.getenv("API_RATE_LIMIT_PER_HOUR", "1000"))
        )

        # Initialize Orchestrator
        logger.info("Creating pipeline orchestrator...")
        
        orchestrator = PipelineOrchestrator(
            asr=asr,
            tts=tts,
            llm=llm,
            nlu=nlu,
            moderator=moderator,
            redis_client=redis_client,
            postgres_client=postgres_client,
            qdrant_client=qdrant_client,
            config_manager=config_manager,
            analytics=analytics,
            data_adapter=data_adapter,
            policy_planner=policy_planner,
            session_manager=session_manager
        )

        # Initialize API Gateway
        logger.info("Starting API Gateway...")
        
        api_gateway = APIGateway(
            orchestrator=orchestrator,
            tenant_manager=tenant_manager,
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", "8000"))
        )

        logger.info("✅ VaaS Platform initialized successfully!")
        
        return api_gateway

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


def main():
    """Main entry point"""
    try:
        # Create necessary directories
        Path("logs").mkdir(exist_ok=True)
        Path("tmp").mkdir(exist_ok=True)
        Path("models").mkdir(exist_ok=True)
        
        # Initialize and run
        logger.info("=" * 60)
        logger.info("Voice-as-a-Service Platform")
        logger.info("Version: 1.0.0")
        logger.info("=" * 60)
        
        # Run async initialization
        api_gateway = asyncio.run(initialize_services())
        
        # Start API server
        api_gateway.run()
        
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()

