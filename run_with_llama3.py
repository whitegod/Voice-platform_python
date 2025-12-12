"""
Voice-as-a-Service - Using Original Architecture
✅ Whisper ASR (local speech-to-text)
✅ Coqui TTS (text-to-speech)
✅ Llama 3 (LLM reasoning)
✅ Rasa (intent detection)
✅ Detoxify (content moderation)
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

# Import all core components as specified
from src.ai_core import WhisperASR, CoquiTTS, LLMProvider, RasaNLU, ContentModerator
from src.ai_core.llm import LLMProviderType

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Core Components with YOUR specifications
print("=" * 70)
print("Initializing Voice-as-a-Service with Original Architecture")
print("=" * 70)
print()

# 1. Whisper ASR - Local, privacy-preserving speech-to-text
print("1. Loading Whisper ASR (local speech recognition)...")
try:
    asr = WhisperASR(
        model_name="base",  # Options: tiny, base, small, medium, large
        device="cpu",       # Use "cuda" if you have GPU
        language="en"
    )
    print("   ✅ Whisper ASR loaded - Privacy-preserving voice input ready")
except Exception as e:
    print(f"   ⚠️  Whisper not available: {e}")
    print("   Install with: pip install openai-whisper")
    asr = None

# 2. Coqui TTS - Text-to-speech for output
print("2. Loading Coqui TTS (speech synthesis)...")
try:
    tts = CoquiTTS(
        model_name="tts_models/en/ljspeech/tacotron2-DDC",
        device="cpu"
    )
    print("   ✅ Coqui TTS loaded - Human-like speech output ready")
except Exception as e:
    print(f"   ⚠️  Coqui TTS not available: {e}")
    print("   Install with: pip install TTS")
    tts = None

# 3. Llama 3 - LLM for reasoning and generation
print("3. Loading Llama 3 (language model for reasoning)...")
try:
    llm = LLMProvider(
        provider=LLMProviderType.LOCAL_LLAMA,
        model_name="llama-3-8b-instruct",
        temperature=0.7
    )
    print("   ✅ Llama 3 loaded - Local reasoning engine ready")
except Exception as e:
    print(f"   ⚠️  Llama 3 not available: {e}")
    print("   Note: Requires llama.cpp or transformers with Llama 3 model")
    print("   For now, using fallback response generation")
    llm = None

# 4. Rasa NLU - Intent detection and slot extraction
print("4. Connecting to Rasa NLU (intent detection)...")
try:
    nlu = RasaNLU(
        rasa_endpoint="http://localhost:5005"
    )
    print("   ✅ Rasa NLU connected - Intent detection ready")
except Exception as e:
    print(f"   ⚠️  Rasa not available: {e}")
    print("   Install Rasa or use offline intent matching")
    nlu = None

# 5. Detoxify - Content moderation
print("5. Loading Detoxify (content moderation)...")
try:
    moderator = ContentModerator(
        model_name="original",
        threshold=0.7
    )
    print("   ✅ Detoxify loaded - Content safety ready")
except Exception as e:
    print(f"   ⚠️  Detoxify not available: {e}")
    print("   Install with: pip install detoxify")
    moderator = None

print()
print("=" * 70)
print("Core Components Status:")
print("=" * 70)
print(f"Whisper ASR:   {'✅ Active' if asr else '❌ Not loaded'}")
print(f"Coqui TTS:     {'✅ Active' if tts else '❌ Not loaded'}")
print(f"Llama 3:       {'✅ Active' if llm else '❌ Not loaded'}")
print(f"Rasa NLU:      {'✅ Active' if nlu else '❌ Not loaded'}")
print(f"Detoxify:      {'✅ Active' if moderator else '❌ Not loaded'}")
print("=" * 70)
print()

# Load domain configurations
import json
DOMAINS = {}
domains_dir = Path("config/domains")
if domains_dir.exists():
    for domain_file in domains_dir.glob("*.json"):
        try:
            with open(domain_file, encoding='utf-8') as f:
                config = json.load(f)
                DOMAINS[config["domain_name"]] = config
        except:
            pass

print(f"✅ Loaded {len(DOMAINS)} domains")
print()

# FastAPI app
app = FastAPI(
    title="Voice-as-a-Service (Original Architecture)",
    description="Using Whisper + Coqui + Llama 3 + Rasa + Detoxify"
)

class TextRequest(BaseModel):
    text: str
    user_id: str
    domain: str
    session_id: Optional[str] = None
    return_audio: bool = False

class ProcessResponse(BaseModel):
    success: bool
    text_response: str
    intent: Optional[str] = None
    entities: Optional[dict] = None
    session_id: Optional[str] = None
    audio_path: Optional[str] = None

# In-memory sessions
sessions = {}

@app.get("/")
async def root():
    return {
        "service": "Voice-as-a-Service (Original Architecture)",
        "version": "1.0.0",
        "components": {
            "whisper_asr": asr is not None,
            "coqui_tts": tts is not None,
            "llama_3": llm is not None,
            "rasa_nlu": nlu is not None,
            "detoxify": moderator is not None
        },
        "domains": len(DOMAINS)
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "architecture": "original",
        "components": {
            "whisper_asr": asr.is_available() if asr else False,
            "coqui_tts": tts.is_available() if tts else False,
            "llama_3": llm.is_available() if llm else False,
            "rasa_nlu": await nlu.health_check() if nlu else False,
            "detoxify": moderator.is_available() if moderator else False
        }
    }

@app.post("/api/v1/process/text", response_model=ProcessResponse)
async def process_text(request: TextRequest):
    """Process using original architecture"""
    import uuid
    
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        # Step 1: Content Moderation (Detoxify)
        if moderator:
            moderation = moderator.moderate(request.text)
            if not moderation["is_safe"]:
                return ProcessResponse(
                    success=False,
                    text_response="I cannot process that request due to content policy.",
                    intent="moderation_failed",
                    entities={},
                    session_id=session_id
                )
        
        # Step 2: Intent Detection (Rasa)
        if nlu:
            nlu_result = await nlu.parse(request.text)
            intent = nlu_result["intent"]["name"]
            entities = nlu_result["slots"]
        else:
            # Fallback: simple intent matching
            intent = "general_query"
            entities = {}
        
        # Step 3: Generate Response (Llama 3)
        domain_config = DOMAINS.get(request.domain, {})
        system_prompt = domain_config.get("system_prompt", "You are a helpful assistant.")
        
        if llm:
            response_text = await llm.generate(
                prompt=request.text,
                system_prompt=system_prompt
            )
        else:
            # Fallback: Use templates
            templates = domain_config.get("response_templates", {})
            response_text = templates.get(intent, 
                domain_config.get("fallback_response", "I'm here to help!"))
        
        # Step 4: Text-to-Speech (Coqui TTS)
        audio_path = None
        if request.return_audio and tts:
            audio_path = f"tmp/response_{session_id}.wav"
            Path("tmp").mkdir(exist_ok=True)
            tts.synthesize(response_text, output_path=audio_path)
        
        return ProcessResponse(
            success=True,
            text_response=response_text,
            intent=intent,
            entities=entities,
            session_id=session_id,
            audio_path=audio_path
        )
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return ProcessResponse(
            success=False,
            text_response=f"Error processing request: {str(e)}",
            intent="error",
            entities={},
            session_id=session_id
        )

@app.post("/api/v1/process/voice")
async def process_voice(
    audio_file: UploadFile = File(...),
    user_id: str = "default",
    domain: str = "real_estate"
):
    """Process voice using Whisper ASR"""
    
    if not asr:
        raise HTTPException(status_code=503, detail="Whisper ASR not available")
    
    # Save uploaded audio
    audio_path = f"tmp/upload_{user_id}.wav"
    Path("tmp").mkdir(exist_ok=True)
    
    with open(audio_path, "wb") as f:
        content = await audio_file.read()
        f.write(content)
    
    # Transcribe with Whisper
    transcription = asr.transcribe(audio_path)
    text = transcription["text"]
    
    # Process the text
    result = await process_text(TextRequest(
        text=text,
        user_id=user_id,
        domain=domain,
        return_audio=True  # Return audio response
    ))
    
    return {
        "transcription": text,
        "response": result.text_response,
        "audio_response": result.audio_path,
        "intent": result.intent
    }

def main():
    print("=" * 70)
    print("Voice-as-a-Service - Original Architecture")
    print("=" * 70)
    print()
    print("Architecture as specified:")
    print("  1. Whisper ASR - Local speech-to-text (privacy)")
    print("  2. Coqui TTS - Human-like speech output")
    print("  3. Llama 3 - Reasoning and generation")
    print("  4. Rasa - Intent detection and slots")
    print("  5. Detoxify - Content moderation")
    print()
    print("Server starting on: http://localhost:8002")
    print("API Docs: http://localhost:8002/docs")
    print()
    print("=" * 70)
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8002)

if __name__ == "__main__":
    main()

