"""
Rasa Natural Language Understanding
Intent recognition and entity extraction
"""

import logging
from typing import Dict, List, Any, Optional
import httpx
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


class RasaNLU:
    """
    Wrapper for Rasa NLU to extract intents and entities from user input.
    """

    def __init__(
        self,
        rasa_endpoint: str = "http://localhost:5005",
        model_path: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize Rasa NLU client.

        Args:
            rasa_endpoint: Rasa server endpoint
            model_path: Path to trained Rasa model
            timeout: Request timeout in seconds
        """
        self.rasa_endpoint = rasa_endpoint.rstrip("/")
        self.model_path = model_path
        self.timeout = timeout
        
        logger.info(f"Initializing Rasa NLU with endpoint: {rasa_endpoint}")

    async def parse(self, text: str, message_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse text to extract intent and entities.

        Args:
            text: Input text to parse
            message_id: Optional message identifier

        Returns:
            Dictionary containing intent, entities, and confidence scores
        """
        try:
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")

            logger.info(f"Parsing text with Rasa: '{text[:100]}...'")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.rasa_endpoint}/model/parse",
                    json={"text": text, "message_id": message_id}
                )
                response.raise_for_status()
                result = response.json()

            parsed = self._format_parse_result(result)
            logger.info(f"Detected intent: {parsed['intent']['name']} "
                       f"(confidence: {parsed['intent']['confidence']:.2f})")
            
            return parsed

        except httpx.HTTPError as e:
            logger.error(f"Rasa HTTP error: {e}")
            # Return fallback result
            return self._get_fallback_result(text)
        except Exception as e:
            logger.error(f"Rasa parsing failed: {e}")
            return self._get_fallback_result(text)

    def _format_parse_result(self, rasa_result: Dict) -> Dict[str, Any]:
        """Format Rasa result into standardized structure"""
        return {
            "text": rasa_result.get("text", ""),
            "intent": {
                "name": rasa_result.get("intent", {}).get("name", "unknown"),
                "confidence": rasa_result.get("intent", {}).get("confidence", 0.0)
            },
            "entities": [
                {
                    "entity": e.get("entity"),
                    "value": e.get("value"),
                    "confidence": e.get("confidence", 1.0),
                    "start": e.get("start"),
                    "end": e.get("end")
                }
                for e in rasa_result.get("entities", [])
            ],
            "intent_ranking": rasa_result.get("intent_ranking", []),
            "slots": self._extract_slots(rasa_result.get("entities", []))
        }

    def _extract_slots(self, entities: List[Dict]) -> Dict[str, Any]:
        """Extract slot values from entities"""
        slots = {}
        for entity in entities:
            entity_name = entity.get("entity")
            entity_value = entity.get("value")
            if entity_name and entity_value:
                slots[entity_name] = entity_value
        return slots

    def _get_fallback_result(self, text: str) -> Dict[str, Any]:
        """Return fallback result when Rasa is unavailable"""
        return {
            "text": text,
            "intent": {
                "name": "nlu_fallback",
                "confidence": 0.0
            },
            "entities": [],
            "intent_ranking": [],
            "slots": {}
        }

    async def train(self, training_data_path: str, domain_path: str, config_path: str):
        """
        Trigger Rasa model training (if Rasa server supports it).

        Args:
            training_data_path: Path to NLU training data
            domain_path: Path to domain.yml
            config_path: Path to config.yml
        """
        try:
            logger.info("Triggering Rasa model training")
            
            # This would call Rasa training API
            # Implementation depends on Rasa version and setup
            logger.warning("Training via API not implemented - train Rasa model separately")
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise

    async def get_tracker(self, sender_id: str) -> Dict[str, Any]:
        """
        Get conversation tracker for a user.

        Args:
            sender_id: User identifier

        Returns:
            Conversation tracker data
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.rasa_endpoint}/conversations/{sender_id}/tracker"
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to get tracker: {e}")
            return {}

    async def health_check(self) -> bool:
        """
        Check if Rasa server is healthy.

        Returns:
            True if server is responding
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.rasa_endpoint}/status")
                response.raise_for_status()
                logger.info("Rasa health check passed")
                return True
        except Exception as e:
            logger.warning(f"Rasa health check failed: {e}")
            return False

    @staticmethod
    def create_training_data(
        intents: List[Dict[str, Any]],
        output_path: str
    ):
        """
        Create Rasa NLU training data file.

        Args:
            intents: List of intent definitions with examples
            output_path: Path to save training data
        """
        nlu_data = {
            "version": "3.1",
            "nlu": []
        }

        for intent_def in intents:
            intent_name = intent_def.get("name")
            examples = intent_def.get("examples", [])
            
            nlu_data["nlu"].append({
                "intent": intent_name,
                "examples": "\n".join([f"- {ex}" for ex in examples])
            })

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            yaml.dump(nlu_data, f)
        
        logger.info(f"Training data saved to: {output_path}")

