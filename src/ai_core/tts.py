"""
Coqui Text-to-Speech
High-quality speech synthesis from text
"""

import logging
from pathlib import Path
from typing import Optional, Union
import torch
from TTS.api import TTS
import soundfile as sf
import numpy as np

logger = logging.getLogger(__name__)


class CoquiTTS:
    """
    Coqui TTS wrapper for converting text to natural-sounding speech.
    """

    def __init__(
        self,
        model_name: str = "tts_models/en/ljspeech/tacotron2-DDC",
        device: str = "cpu",
    ):
        """
        Initialize Coqui TTS model.

        Args:
            model_name: Coqui TTS model identifier
            device: Device to run on (cpu, cuda)
        """
        self.model_name = model_name
        self.device = device
        self.tts = None
        
        logger.info(f"Initializing Coqui TTS with model: {model_name}")
        self._load_model()

    def _load_model(self):
        """Load the TTS model"""
        try:
            self.tts = TTS(
                model_name=self.model_name,
                progress_bar=False,
                gpu=(self.device == "cuda")
            )
            logger.info(f"Coqui TTS model '{self.model_name}' loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load TTS model: {e}")
            raise

    def synthesize(
        self,
        text: str,
        output_path: Optional[Union[str, Path]] = None,
        speaker: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Union[Path, np.ndarray]:
        """
        Convert text to speech.

        Args:
            text: Text to synthesize
            output_path: Path to save audio file (if None, returns array)
            speaker: Speaker name for multi-speaker models
            language: Language code for multi-lingual models

        Returns:
            Path to saved file or numpy array of audio
        """
        try:
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")

            logger.info(f"Synthesizing speech for text: '{text[:100]}...'")

            # Prepare TTS arguments
            tts_kwargs = {}
            if speaker:
                tts_kwargs["speaker"] = speaker
            if language:
                tts_kwargs["language"] = language

            if output_path:
                # Save directly to file
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                self.tts.tts_to_file(
                    text=text,
                    file_path=str(output_path),
                    **tts_kwargs
                )
                
                logger.info(f"Speech saved to: {output_path}")
                return output_path
            else:
                # Return as numpy array
                audio_array = self.tts.tts(text=text, **tts_kwargs)
                logger.info("Speech synthesized to array")
                return np.array(audio_array)

        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
            raise

    def synthesize_streaming(
        self,
        text: str,
        chunk_size: int = 512,
        **kwargs
    ):
        """
        Generate speech in streaming chunks (placeholder for future implementation).

        Args:
            text: Text to synthesize
            chunk_size: Size of audio chunks
            **kwargs: Additional TTS parameters

        Yields:
            Audio chunks as numpy arrays
        """
        # Note: Implement streaming if needed for real-time applications
        logger.warning("Streaming not yet implemented, using batch synthesis")
        audio = self.synthesize(text, output_path=None, **kwargs)
        
        # Yield in chunks
        for i in range(0, len(audio), chunk_size):
            yield audio[i:i + chunk_size]

    def save_audio(
        self,
        audio_array: np.ndarray,
        output_path: Union[str, Path],
        sample_rate: int = 22050
    ) -> Path:
        """
        Save audio array to file.

        Args:
            audio_array: Audio data as numpy array
            output_path: Path to save file
            sample_rate: Sample rate of audio

        Returns:
            Path to saved file
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            sf.write(str(output_path), audio_array, sample_rate)
            logger.info(f"Audio saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to save audio: {e}")
            raise

    def is_available(self) -> bool:
        """Check if TTS is ready to use"""
        return self.tts is not None

    def get_speakers(self) -> Optional[list]:
        """Get available speakers for multi-speaker models"""
        try:
            if hasattr(self.tts, "speakers") and self.tts.speakers:
                return self.tts.speakers
            return None
        except Exception:
            return None

    def get_languages(self) -> Optional[list]:
        """Get available languages for multi-lingual models"""
        try:
            if hasattr(self.tts, "languages") and self.tts.languages:
                return self.tts.languages
            return None
        except Exception:
            return None

