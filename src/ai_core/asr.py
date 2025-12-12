"""
Whisper Automatic Speech Recognition
Local, privacy-preserving speech-to-text conversion
"""

import whisper
import torch
import logging
from pathlib import Path
from typing import Optional, Union
import soundfile as sf
import numpy as np

logger = logging.getLogger(__name__)


class WhisperASR:
    """
    Whisper ASR wrapper for converting speech to text locally.
    Ensures privacy by processing audio without external API calls.
    """

    def __init__(
        self,
        model_name: str = "base",
        device: str = "cpu",
        language: str = "en",
    ):
        """
        Initialize Whisper ASR model.

        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
            device: Device to run on (cpu, cuda)
            language: Default language for transcription
        """
        self.model_name = model_name
        self.device = device
        self.language = language
        self.model = None
        
        logger.info(f"Initializing Whisper ASR with model: {model_name}")
        self._load_model()

    def _load_model(self):
        """Load the Whisper model"""
        try:
            self.model = whisper.load_model(
                self.model_name,
                device=self.device
            )
            logger.info(f"Whisper model '{self.model_name}' loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    def transcribe(
        self,
        audio_path: Union[str, Path],
        language: Optional[str] = None,
        **kwargs
    ) -> dict:
        """
        Transcribe audio file to text.

        Args:
            audio_path: Path to audio file
            language: Language code (overrides default)
            **kwargs: Additional whisper transcribe parameters

        Returns:
            dict: Transcription result containing text and metadata
        """
        try:
            audio_path = Path(audio_path)
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")

            logger.info(f"Transcribing audio: {audio_path}")
            
            # Transcribe using Whisper
            result = self.model.transcribe(
                str(audio_path),
                language=language or self.language,
                **kwargs
            )

            transcription = {
                "text": result["text"].strip(),
                "language": result.get("language", self.language),
                "segments": result.get("segments", []),
                "duration": self._get_audio_duration(audio_path),
            }

            logger.info(f"Transcription completed: '{transcription['text'][:100]}...'")
            return transcription

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    def transcribe_audio_array(
        self,
        audio_array: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[str] = None,
        **kwargs
    ) -> dict:
        """
        Transcribe audio from numpy array.

        Args:
            audio_array: Audio data as numpy array
            sample_rate: Sample rate of the audio
            language: Language code
            **kwargs: Additional whisper parameters

        Returns:
            dict: Transcription result
        """
        try:
            logger.info("Transcribing audio array")
            
            # Whisper expects 16kHz audio
            if sample_rate != 16000:
                logger.warning(f"Resampling from {sample_rate}Hz to 16000Hz")
                # Note: In production, use librosa.resample here
                
            result = self.model.transcribe(
                audio_array,
                language=language or self.language,
                **kwargs
            )

            return {
                "text": result["text"].strip(),
                "language": result.get("language", self.language),
                "segments": result.get("segments", []),
            }

        except Exception as e:
            logger.error(f"Array transcription failed: {e}")
            raise

    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get audio file duration in seconds"""
        try:
            audio_data, sample_rate = sf.read(str(audio_path))
            duration = len(audio_data) / sample_rate
            return duration
        except Exception as e:
            logger.warning(f"Could not get audio duration: {e}")
            return 0.0

    def is_available(self) -> bool:
        """Check if ASR is ready to use"""
        return self.model is not None

    def get_supported_languages(self) -> list:
        """Get list of supported languages"""
        return whisper.tokenizer.LANGUAGES.keys()

