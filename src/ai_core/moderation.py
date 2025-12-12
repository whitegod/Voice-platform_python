"""
Content Moderation using Detoxify
Ensures input safety and appropriateness
"""

import logging
from typing import Dict, Optional
from detoxify import Detoxify

logger = logging.getLogger(__name__)


class ContentModerator:
    """
    Content moderation using Detoxify to filter toxic, inappropriate content.
    """

    def __init__(
        self,
        model_name: str = "original",
        threshold: float = 0.7
    ):
        """
        Initialize content moderator.

        Args:
            model_name: Detoxify model (original, unbiased, multilingual)
            threshold: Toxicity threshold (0-1)
        """
        self.model_name = model_name
        self.threshold = threshold
        self.model = None
        
        logger.info(f"Initializing Content Moderator with model: {model_name}")
        self._load_model()

    def _load_model(self):
        """Load Detoxify model"""
        try:
            self.model = Detoxify(self.model_name)
            logger.info("Content moderation model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load moderation model: {e}")
            raise

    def moderate(self, text: str) -> Dict[str, any]:
        """
        Moderate text content for toxicity.

        Args:
            text: Text to moderate

        Returns:
            Dictionary with moderation results and toxicity scores
        """
        try:
            if not text or not text.strip():
                return {
                    "is_safe": True,
                    "scores": {},
                    "flagged_categories": [],
                    "message": "Empty text"
                }

            logger.info(f"Moderating text: '{text[:100]}...'")

            # Get toxicity scores
            scores = self.model.predict(text)

            # Check which categories exceed threshold
            flagged = []
            for category, score in scores.items():
                if score > self.threshold:
                    flagged.append(category)

            is_safe = len(flagged) == 0

            result = {
                "is_safe": is_safe,
                "scores": scores,
                "flagged_categories": flagged,
                "message": self._get_moderation_message(is_safe, flagged)
            }

            if not is_safe:
                logger.warning(f"Content flagged: {', '.join(flagged)}")
            else:
                logger.info("Content passed moderation")

            return result

        except Exception as e:
            logger.error(f"Moderation failed: {e}")
            # Fail open - allow content if moderation fails
            return {
                "is_safe": True,
                "scores": {},
                "flagged_categories": [],
                "message": "Moderation check failed, content allowed"
            }

    def moderate_batch(self, texts: list) -> list:
        """
        Moderate multiple texts.

        Args:
            texts: List of texts to moderate

        Returns:
            List of moderation results
        """
        try:
            logger.info(f"Moderating batch of {len(texts)} texts")
            
            # Detoxify supports batch prediction
            scores_batch = self.model.predict(texts)
            
            results = []
            for i, text in enumerate(texts):
                scores = {k: v[i] for k, v in scores_batch.items()}
                
                flagged = [cat for cat, score in scores.items() 
                          if score > self.threshold]
                is_safe = len(flagged) == 0
                
                results.append({
                    "is_safe": is_safe,
                    "scores": scores,
                    "flagged_categories": flagged,
                    "message": self._get_moderation_message(is_safe, flagged)
                })
            
            return results

        except Exception as e:
            logger.error(f"Batch moderation failed: {e}")
            # Return safe results if moderation fails
            return [{"is_safe": True, "scores": {}, "flagged_categories": [], 
                    "message": "Moderation failed"} for _ in texts]

    def _get_moderation_message(self, is_safe: bool, flagged: list) -> str:
        """Generate human-readable moderation message"""
        if is_safe:
            return "Content is appropriate"
        else:
            categories = ", ".join(flagged)
            return f"Content flagged for: {categories}"

    def set_threshold(self, threshold: float):
        """
        Update moderation threshold.

        Args:
            threshold: New threshold (0-1)
        """
        if not 0 <= threshold <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        
        self.threshold = threshold
        logger.info(f"Moderation threshold updated to: {threshold}")

    def get_categories(self) -> list:
        """Get list of toxicity categories detected by the model"""
        categories = [
            "toxicity",
            "severe_toxicity",
            "obscene",
            "threat",
            "insult",
            "identity_attack"
        ]
        
        if self.model_name == "unbiased":
            categories.extend(["sexual_explicit"])
        
        return categories

    def is_available(self) -> bool:
        """Check if moderation is ready"""
        return self.model is not None

