"""
Large Language Model Provider
Unified interface for multiple LLM providers (OpenAI, Vertex AI, Llama 3)
"""

import logging
from typing import Optional, List, Dict, Any
from enum import Enum
import os

# LLM Provider imports
import openai
from anthropic import Anthropic
try:
    from google.cloud import aiplatform
    from vertexai.preview.generative_models import GenerativeModel
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False

logger = logging.getLogger(__name__)


class LLMProviderType(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    VERTEX_AI = "vertex_ai"
    ANTHROPIC = "anthropic"
    LOCAL_LLAMA = "local_llama"


class LLMProvider:
    """
    Unified interface for interacting with various LLM providers.
    Handles reasoning, response generation, and action planning.
    """

    def __init__(
        self,
        provider: LLMProviderType = LLMProviderType.OPENAI,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ):
        """
        Initialize LLM provider.

        Args:
            provider: LLM provider type
            model_name: Specific model name (provider-dependent)
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            **kwargs: Additional provider-specific parameters
        """
        self.provider = provider
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.model_name = model_name or self._get_default_model(provider)
        self.client = None
        
        logger.info(f"Initializing LLM Provider: {provider.value} with model {self.model_name}")
        self._initialize_client(**kwargs)

    def _get_default_model(self, provider: LLMProviderType) -> str:
        """Get default model for provider"""
        defaults = {
            LLMProviderType.OPENAI: "gpt-4-turbo-preview",
            LLMProviderType.VERTEX_AI: "gemini-pro",
            LLMProviderType.ANTHROPIC: "claude-3-sonnet-20240229",
            LLMProviderType.LOCAL_LLAMA: "llama-3-8b-instruct",
        }
        return defaults.get(provider, "gpt-4-turbo-preview")

    def _initialize_client(self, **kwargs):
        """Initialize the specific LLM client"""
        try:
            if self.provider == LLMProviderType.OPENAI:
                self.client = openai.OpenAI(
                    api_key=kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
                )
                
            elif self.provider == LLMProviderType.ANTHROPIC:
                self.client = Anthropic(
                    api_key=kwargs.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
                )
                
            elif self.provider == LLMProviderType.VERTEX_AI:
                if not VERTEX_AVAILABLE:
                    raise ImportError("Vertex AI libraries not installed")
                project_id = kwargs.get("project_id") or os.getenv("GOOGLE_CLOUD_PROJECT")
                location = kwargs.get("location") or os.getenv("VERTEX_AI_LOCATION", "us-central1")
                aiplatform.init(project=project_id, location=location)
                self.client = GenerativeModel(self.model_name)
                
            elif self.provider == LLMProviderType.LOCAL_LLAMA:
                # Placeholder for local Llama implementation
                logger.warning("Local Llama support is placeholder - implement with transformers")
                self.client = None
                
            logger.info(f"LLM client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            raise

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> str:
        """
        Generate text completion from prompt.

        Args:
            prompt: User prompt
            system_prompt: System instructions
            context: Conversation history
            **kwargs: Additional generation parameters

        Returns:
            Generated text response
        """
        try:
            logger.info(f"Generating response with {self.provider.value}")
            
            if self.provider == LLMProviderType.OPENAI:
                return await self._generate_openai(prompt, system_prompt, context, **kwargs)
            elif self.provider == LLMProviderType.ANTHROPIC:
                return await self._generate_anthropic(prompt, system_prompt, context, **kwargs)
            elif self.provider == LLMProviderType.VERTEX_AI:
                return await self._generate_vertex(prompt, system_prompt, context, **kwargs)
            elif self.provider == LLMProviderType.LOCAL_LLAMA:
                return await self._generate_local(prompt, system_prompt, context, **kwargs)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

    async def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        context: Optional[List[Dict]],
        **kwargs
    ) -> str:
        """Generate using OpenAI API"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        if context:
            messages.extend(context)
            
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
        )

        return response.choices[0].message.content

    async def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        context: Optional[List[Dict]],
        **kwargs
    ) -> str:
        """Generate using Anthropic API"""
        messages = []
        
        if context:
            messages.extend(context)
            
        messages.append({"role": "user", "content": prompt})

        response = self.client.messages.create(
            model=self.model_name,
            system=system_prompt or "",
            messages=messages,
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
        )

        return response.content[0].text

    async def _generate_vertex(
        self,
        prompt: str,
        system_prompt: Optional[str],
        context: Optional[List[Dict]],
        **kwargs
    ) -> str:
        """Generate using Google Vertex AI"""
        full_prompt = ""
        
        if system_prompt:
            full_prompt += f"System: {system_prompt}\n\n"
            
        if context:
            for msg in context:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                full_prompt += f"{role}: {content}\n"
                
        full_prompt += f"User: {prompt}\n\nAssistant:"

        response = self.client.generate_content(
            full_prompt,
            generation_config={
                "temperature": kwargs.get("temperature", self.temperature),
                "max_output_tokens": kwargs.get("max_tokens", self.max_tokens),
            }
        )

        return response.text

    async def _generate_local(
        self,
        prompt: str,
        system_prompt: Optional[str],
        context: Optional[List[Dict]],
        **kwargs
    ) -> str:
        """Generate using local Llama model (placeholder)"""
        # TODO: Implement with transformers pipeline
        logger.warning("Local Llama generation not implemented")
        return "Local Llama response (not implemented)"

    def create_action_plan(
        self,
        user_intent: str,
        entities: Dict[str, Any],
        domain_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create an action plan for executing backend API calls.

        Args:
            user_intent: Identified user intent
            entities: Extracted entities
            domain_context: Domain-specific context

        Returns:
            Structured action plan
        """
        # This would use the LLM to create a structured plan
        # For now, return a structured format
        return {
            "intent": user_intent,
            "entities": entities,
            "actions": [],
            "requires_api_call": False,
            "response_template": ""
        }

    def is_available(self) -> bool:
        """Check if LLM provider is ready"""
        return self.client is not None

