"""
Voice-as-a-Service - Simplified Version (No Docker Required!)
Run this for a lightweight version using only OpenAI and basic Python
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Dict, Any

# Only essential imports
try:
    from fastapi import FastAPI, HTTPException, Header
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    import uvicorn
    import openai
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.run(["pip", "install", "fastapi", "uvicorn", "openai", "pydantic", "python-dotenv", "httpx"])
    print("Please run the script again!")
    exit(0)

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key or not openai.api_key.startswith("sk-"):
    print("❌ ERROR: OpenAI API key not configured!")
    print("Edit .env and add: OPENAI_API_KEY=sk-your-key-here")
    exit(1)

# In-memory storage (replaces Redis/PostgreSQL)
sessions = {}
# Load API keys from environment or use demo keys
demo_api_keys = os.getenv("DEMO_API_KEYS", "demo_key_12345:demo_tenant")
api_keys = {}
for key_pair in demo_api_keys.split(","):
    if ":" in key_pair:
        key, tenant = key_pair.strip().split(":", 1)
        api_keys[key] = tenant

# Load domain configurations
DOMAINS = {}
domains_dir = Path("config/domains")
if domains_dir.exists():
    for domain_file in domains_dir.glob("*.json"):
        try:
            with open(domain_file) as f:
                config = json.load(f)
                DOMAINS[config["domain_name"]] = config
                logger.info(f"Loaded domain: {config['domain_name']}")
        except Exception as e:
            logger.warning(f"Could not load {domain_file}: {e}")

logger.info(f"Loaded {len(DOMAINS)} domains")

# Request/Response Models
class TextRequest(BaseModel):
    text: str
    user_id: str
    domain: str
    session_id: Optional[str] = None

class ProcessResponse(BaseModel):
    success: bool
    text_response: str
    intent: Optional[str] = None
    entities: Optional[dict] = None
    session_id: Optional[str] = None

# FastAPI app
app = FastAPI(
    title="Voice-as-a-Service (Simplified)",
    description="Lightweight version without Docker - Uses OpenAI for all AI tasks",
    version="1.0.0-simple"
)

async def verify_api_key(authorization: Optional[str] = Header(None)) -> str:
    """Simple API key verification"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        scheme, api_key = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError()
    except:
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    tenant_id = api_keys.get(api_key)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return tenant_id

async def process_with_openai(text: str, domain: str, session_id: Optional[str]) -> Dict[str, Any]:
    """Process request using OpenAI"""
    
    # Get domain config
    domain_config = DOMAINS.get(domain)
    if not domain_config:
        return {
            "text_response": f"Domain '{domain}' not found. Available: {', '.join(DOMAINS.keys())}",
            "intent": "error"
        }
    
    # Get system prompt
    system_prompt = domain_config.get("system_prompt", "You are a helpful assistant.")
    
    # Get conversation history
    history = sessions.get(session_id, []) if session_id else []
    
    # Build messages
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": text})
    
    # Call OpenAI
    try:
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
            messages=messages,
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "500"))
        )
        
        ai_response = response.choices[0].message.content
        
        # Simple intent extraction (ask OpenAI)
        intent_prompt = f"Extract the primary intent from this text in one word: '{text}'\n\nIntents available: {', '.join([i['name'] for i in domain_config.get('intents', [])])}\n\nIntent:"
        
        intent_response = client.chat.completions.create(
            model=os.getenv("OPENAI_INTENT_MODEL", "gpt-3.5-turbo"),
            messages=[{"role": "user", "content": intent_prompt}],
            temperature=0,
            max_tokens=int(os.getenv("INTENT_MAX_TOKENS", "10"))
        )
        
        intent = intent_response.choices[0].message.content.strip()
        
        # Update session
        if session_id:
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append({"role": "user", "content": text})
            sessions[session_id].append({"role": "assistant", "content": ai_response})
            # Keep last 10 messages
            sessions[session_id] = sessions[session_id][-10:]
        
        return {
            "text_response": ai_response,
            "intent": intent,
            "entities": {},
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return {
            "text_response": f"Sorry, I encountered an error: {str(e)}",
            "intent": "error",
            "entities": {},
            "session_id": session_id
        }

# Routes
@app.get("/")
async def root():
    return {
        "service": "Voice-as-a-Service (Simplified)",
        "version": "1.0.0-simple",
        "note": "Running without Docker - using OpenAI for all AI tasks",
        "domains": len(DOMAINS)
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "mode": "simplified",
        "domains_loaded": len(DOMAINS),
        "openai_configured": bool(openai.api_key)
    }

@app.get("/api/v1/domains")
async def list_domains():
    from fastapi import Depends
    return {"domains": list(DOMAINS.keys())}

@app.post("/api/v1/process/text", response_model=ProcessResponse)
async def process_text(request: TextRequest):
    """Process text without complex infrastructure"""
    try:
        logger.info(f"Processing: '{request.text}' for domain: {request.domain}")
        
        # Generate session ID if not provided
        if not request.session_id:
            import uuid
            request.session_id = str(uuid.uuid4())
        
        # Process with OpenAI
        result = await process_with_openai(
            text=request.text,
            domain=request.domain,
            session_id=request.session_id
        )
        
        return ProcessResponse(
            success=True,
            **result
        )
        
    except Exception as e:
        logger.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def main():
    """Run the simplified server"""
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    # Get first API key for display
    first_api_key = list(api_keys.keys())[0] if api_keys else "demo_key_12345"
    
    print("=" * 70)
    print("Voice-as-a-Service Platform - Simplified Mode")
    print("=" * 70)
    print()
    print("✅ Running WITHOUT Docker!")
    print(f"✅ Loaded {len(DOMAINS)} domains")
    print("✅ Using OpenAI for all AI tasks")
    print()
    print(f"API will be available at: http://localhost:{port}")
    print(f"API Docs: http://localhost:{port}/docs")
    print()
    print(f"Test API key: {first_api_key}")
    print()
    print("Example request:")
    print(f'  curl -X POST "http://localhost:{port}/api/v1/process/text" \\')
    print(f'    -H "Authorization: Bearer {first_api_key}" \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"text": "test", "user_id": "user1", "domain": "customer_support"}\'')
    print()
    print("=" * 70)
    print()
    
    # Run server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )

if __name__ == "__main__":
    main()

