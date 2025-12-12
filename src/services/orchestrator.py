"""
Pipeline Orchestrator
Central coordinator for the VaaS platform workflow
"""

import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
import time
import uuid

from ..ai_core import WhisperASR, CoquiTTS, LLMProvider, RasaNLU, ContentModerator
from ..data_layer import RedisClient, PostgresClient, QdrantVectorDB
from .session_manager import SessionManager
from .config_manager import ConfigManager
from .analytics import AnalyticsService
from .data_adapter import DataAdapter
from .policy_planner import PolicyPlanner

logger = logging.getLogger(__name__)


class ProcessingResult:
    """Result of processing a user request"""
    
    def __init__(
        self,
        text_response: str,
        audio_response: Optional[Path] = None,
        intent: Optional[str] = None,
        entities: Optional[Dict] = None,
        api_response: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ):
        self.text_response = text_response
        self.audio_response = audio_response
        self.intent = intent
        self.entities = entities
        self.api_response = api_response
        self.metadata = metadata or {}


class PipelineOrchestrator:
    """
    Central orchestrator coordinating all VaaS services.
    Manages the complete data flow from input to response.
    """

    def __init__(
        self,
        asr: WhisperASR,
        tts: CoquiTTS,
        llm: LLMProvider,
        nlu: RasaNLU,
        moderator: ContentModerator,
        redis_client: RedisClient,
        postgres_client: PostgresClient,
        qdrant_client: QdrantVectorDB,
        config_manager: ConfigManager,
        analytics: AnalyticsService,
        data_adapter: DataAdapter,
        policy_planner: PolicyPlanner,
        session_manager: SessionManager
    ):
        """Initialize orchestrator with all required services"""
        self.asr = asr
        self.tts = tts
        self.llm = llm
        self.nlu = nlu
        self.moderator = moderator
        self.redis = redis_client
        self.postgres = postgres_client
        self.qdrant = qdrant_client
        self.config_manager = config_manager
        self.analytics = analytics
        self.data_adapter = data_adapter
        self.policy_planner = policy_planner
        self.session_manager = session_manager
        
        logger.info("PipelineOrchestrator initialized")

    async def process_voice(
        self,
        audio_path: Union[str, Path],
        user_id: str,
        tenant_id: str,
        domain: str,
        session_id: Optional[str] = None,
        return_audio: bool = True
    ) -> ProcessingResult:
        """
        Process voice input through complete pipeline.

        Args:
            audio_path: Path to audio file
            user_id: User identifier
            tenant_id: Tenant identifier
            domain: Domain name
            session_id: Existing session ID
            return_audio: Whether to generate audio response

        Returns:
            ProcessingResult with text and optionally audio response
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing voice input for user {user_id} in domain {domain}")

            # Step 1: Speech to Text (ASR)
            asr_result = self.asr.transcribe(audio_path)
            text = asr_result["text"]
            
            logger.info(f"Transcribed: '{text}'")

            # Process as text
            result = await self.process_text(
                text=text,
                user_id=user_id,
                tenant_id=tenant_id,
                domain=domain,
                session_id=session_id
            )

            # Generate audio response if requested
            if return_audio and result.text_response:
                audio_output = Path(f"tmp/response_{uuid.uuid4()}.wav")
                audio_output.parent.mkdir(parents=True, exist_ok=True)
                
                self.tts.synthesize(
                    result.text_response,
                    output_path=audio_output
                )
                result.audio_response = audio_output

            # Log analytics
            response_time = time.time() - start_time
            await self.analytics.log_response(
                tenant_id=tenant_id,
                domain=domain,
                response_time=response_time,
                success=True,
                metadata={"input_type": "voice"}
            )

            return result

        except Exception as e:
            logger.error(f"Voice processing failed: {e}")
            await self.analytics.log_error(
                tenant_id=tenant_id,
                error_type="voice_processing_error",
                error_message=str(e)
            )
            raise

    async def process_text(
        self,
        text: str,
        user_id: str,
        tenant_id: str,
        domain: str,
        session_id: Optional[str] = None
    ) -> ProcessingResult:
        """
        Process text input through complete pipeline.

        Args:
            text: Input text
            user_id: User identifier
            tenant_id: Tenant identifier
            domain: Domain name
            session_id: Existing session ID

        Returns:
            ProcessingResult with response
        """
        start_time = time.time()
        message_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Processing text: '{text[:100]}...'")

            # Get or create session
            if not session_id:
                session_id = await self.session_manager.create_session(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    domain=domain
                )
            
            # Step 1: Content Moderation
            moderation_result = self.moderator.moderate(text)
            
            await self.analytics.log_moderation(
                tenant_id=tenant_id,
                is_safe=moderation_result["is_safe"],
                flagged_categories=moderation_result["flagged_categories"]
            )

            if not moderation_result["is_safe"]:
                logger.warning("Content failed moderation")
                return ProcessingResult(
                    text_response="I'm sorry, but I cannot process that request.",
                    intent="moderation_failed",
                    metadata={"moderation": moderation_result}
                )

            # Step 2: Natural Language Understanding (Rasa)
            nlu_result = await self.nlu.parse(text, message_id=message_id)
            intent = nlu_result["intent"]["name"]
            entities = nlu_result["slots"]
            
            logger.info(f"Intent: {intent}, Entities: {entities}")

            # Step 3: Retrieval-Augmented Generation (Optional)
            domain_config = self.config_manager.get_config(domain)
            retrieved_context = []
            
            if domain_config and domain_config.context_retrieval.enabled:
                retrieved_context = await self.qdrant.search(
                    query=text,
                    limit=domain_config.context_retrieval.top_k,
                    tenant_id=tenant_id,
                    collection_name=domain_config.context_retrieval.collection_name
                )
                logger.info(f"Retrieved {len(retrieved_context)} context items")

            # Step 4: Get conversation history
            history = await self.session_manager.get_history(session_id, limit=10)
            
            # Step 5: LLM Reasoning
            system_prompt = self.config_manager.get_system_prompt(domain)
            
            # Build context for LLM
            context_text = ""
            if retrieved_context:
                context_text = "\n\nRelevant Context:\n"
                for ctx in retrieved_context:
                    context_text += f"- {ctx['text']}\n"

            # Build conversation context
            conversation_context = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in history
            ]

            # Create action plan
            plan = {
                "intent": intent,
                "entities": entities,
                "requires_api_call": False,
                "actions": []
            }

            # Check if intent requires API call
            intent_config = self.config_manager.get_intent_config(domain, intent)
            if intent_config and intent_config.api_endpoint:
                plan["requires_api_call"] = True
                plan["actions"].append({
                    "type": "api_call",
                    "name": intent,
                    "config": intent_config
                })

            # Step 6: Policy Validation
            is_valid, violations = await self.policy_planner.validate_plan(
                tenant_id=tenant_id,
                plan=plan,
                context={
                    "moderation_result": moderation_result,
                    "session_id": session_id
                }
            )

            if not is_valid:
                logger.warning(f"Plan validation failed: {violations}")
                return ProcessingResult(
                    text_response="I'm unable to complete that request at this time.",
                    intent=intent,
                    entities=entities,
                    metadata={"violations": [v.message for v in violations]}
                )

            # Step 7: Execute actions
            api_response = None
            if plan["requires_api_call"] and intent_config:
                api_response = await self.data_adapter.call_with_config(
                    intent_config=intent_config,
                    entities=entities,
                    context={"session_id": session_id}
                )
                
                await self.analytics.log_api_call(
                    tenant_id=tenant_id,
                    endpoint=intent_config.api_endpoint,
                    method=intent_config.api_method,
                    status_code=api_response.get("status_code", 0),
                    response_time=api_response.get("response_time", 0)
                )

            # Step 8: Generate natural conversational response
            # Always use LLM for natural conversation, never technical templates
            
            # Build conversation-aware prompt
            if api_response and api_response.get("success"):
                # API call succeeded - incorporate results naturally
                prompt = f"""{context_text}

Current conversation:
User: {text}

[Backend API returned: {api_response.get('data')}]

Respond naturally and conversationally. Don't mention technical terms, API calls, or intent names. 
If you found results, share them enthusiastically. If you need more info, ask friendly questions.
Keep it brief and human."""
            else:
                # No API call or it failed - continue conversation naturally
                prompt = f"""{context_text}

User: {text}
Intent detected: {intent}
Information captured: {entities}

Respond naturally as a helpful real estate agent. 
- If the user is looking for property, engage with what they've told you and ask for any missing details (budget, location, bedrooms, etc.)
- If they're greeting you, greet back warmly
- If info is missing, ask conversationally
- Never list technical intents or capabilities
- Keep it brief, warm, and natural like texting a friend"""
            
            response_text = await self.llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                context=conversation_context
            )

            # Step 9: Save to session and database
            await self.session_manager.add_message(
                session_id=session_id,
                role="user",
                content=text,
                intent=intent,
                entities=entities
            )
            
            await self.session_manager.add_message(
                session_id=session_id,
                role="assistant",
                content=response_text
            )

            # Save to Postgres
            await self.postgres.save_message(
                message_id=message_id,
                conversation_id=session_id,
                role="user",
                content=text,
                intent=intent,
                entities=entities,
                moderation_result=moderation_result
            )

            # Log analytics
            response_time = time.time() - start_time
            await self.analytics.log_request(
                tenant_id=tenant_id,
                domain=domain,
                intent=intent,
                user_id=user_id,
                session_id=session_id
            )
            
            await self.analytics.log_response(
                tenant_id=tenant_id,
                domain=domain,
                response_time=response_time,
                success=True,
                metadata={"input_type": "text"}
            )

            logger.info(f"Request processed successfully in {response_time:.2f}s")

            return ProcessingResult(
                text_response=response_text,
                intent=intent,
                entities=entities,
                api_response=api_response,
                metadata={
                    "session_id": session_id,
                    "response_time": response_time,
                    "retrieved_context_count": len(retrieved_context)
                }
            )

        except Exception as e:
            logger.error(f"Text processing failed: {e}")
            await self.analytics.log_error(
                tenant_id=tenant_id,
                error_type="text_processing_error",
                error_message=str(e),
                context={"text": text[:100]}
            )
            
            # Return fallback response
            fallback = "I'm sorry, I encountered an error processing your request."
            if domain_config:
                fallback = domain_config.fallback_response
            
            return ProcessingResult(
                text_response=fallback,
                metadata={"error": str(e)}
            )

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all services"""
        health = {
            "orchestrator": "healthy",
            "asr": self.asr.is_available(),
            "tts": self.tts.is_available(),
            "llm": self.llm.is_available(),
            "moderator": self.moderator.is_available(),
            "redis": await self.redis.health_check(),
            "postgres": await self.postgres.health_check(),
            "qdrant": await self.qdrant.health_check(),
            "nlu": await self.nlu.health_check()
        }
        
        health["overall"] = all(
            v for k, v in health.items() if k != "orchestrator"
        )
        
        return health

