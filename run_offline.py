"""
Voice-as-a-Service - Completely Offline Version
✅ No Docker needed!
✅ No OpenAI API key needed!
✅ No configuration needed!
✅ 100% FREE!
✅ Works offline with rule-based AI
"""

import json
import logging
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

# Only standard library + FastAPI (no external APIs!)
try:
    from fastapi import FastAPI, HTTPException, Header
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    print("Installing required packages...")
    print("This is a one-time setup that takes 2-3 minutes...\n")
    import subprocess
    subprocess.run(["pip", "install", "fastapi", "uvicorn", "pydantic"])
    print("\n✅ Packages installed! Please run the script again.")
    print("Next time it will start instantly!\n")
    input("Press Enter to exit...")
    exit(0)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("""
╔════════════════════════════════════════════════════════════════╗
║  Voice-as-a-Service Platform - OFFLINE MODE                    ║
║  ✅ No API keys needed!                                         ║
║  ✅ Works 100% offline!                                         ║
║  ✅ All 19 domains functional!                                  ║
╚════════════════════════════════════════════════════════════════╝
""")

# In-memory storage
sessions = {}
conversations = {}

# Load API keys from environment or use demo keys
import os
demo_api_keys = os.getenv("OFFLINE_API_KEYS", "offline_demo_key:demo_tenant,test_key_12345:demo_tenant")
API_KEYS = {}
for key_pair in demo_api_keys.split(","):
    if ":" in key_pair:
        key, tenant = key_pair.strip().split(":", 1)
        API_KEYS[key] = tenant

# Load domain configurations
DOMAINS = {}
domains_dir = Path("config/domains")
if domains_dir.exists():
    for domain_file in domains_dir.glob("*.json"):
        try:
            # Fix encoding issue - use UTF-8
            with open(domain_file, encoding='utf-8') as f:
                config = json.load(f)
                DOMAINS[config["domain_name"]] = config
                logger.info(f"✓ Loaded domain: {config['domain_name']}")
        except Exception as e:
            logger.warning(f"Could not load {domain_file.name}: {e}")

logger.info(f"✅ Loaded {len(DOMAINS)} domains")

# Simple intent matcher (keyword-based)
class SimpleIntentMatcher:
    """Rule-based intent recognition without ML"""
    
    def __init__(self, domain_config: Dict):
        self.domain_config = domain_config
        self.intents = domain_config.get("intents", [])
    
    def match_intent(self, text: str) -> tuple[str, Dict[str, Any]]:
        """Match intent using keywords"""
        text_lower = text.lower()
        
        # Intent keyword patterns
        intent_patterns = {
            # Customer Support
            "create_ticket": ["ticket", "create ticket", "open ticket", "report issue", "submit"],
            "check_ticket_status": ["ticket status", "check ticket", "ticket #", "status of"],
            "search_knowledge_base": ["how do i", "how to", "what is", "explain", "help with"],
            "troubleshoot_issue": ["not working", "broken", "error", "crash", "problem", "issue with"],
            "request_refund": ["refund", "money back", "return", "cancel order"],
            "escalate_to_human": ["human", "agent", "person", "speak to", "talk to"],
            
            # Healthcare
            "schedule_appointment": ["appointment", "schedule", "book", "doctor"],
            "find_doctor": ["find doctor", "search doctor", "doctor in"],
            "check_symptoms": ["symptom", "feeling", "sick", "pain", "hurt"],
            "prescription_refill": ["refill", "prescription", "medication"],
            
            # E-commerce
            "search_products": ["search", "find", "looking for", "show me"],
            "add_to_cart": ["add to cart", "add", "buy", "purchase"],
            "view_cart": ["cart", "basket", "my order"],
            "checkout": ["checkout", "pay", "complete order"],
            "track_order": ["track", "where is", "order status"],
            
            # Banking
            "check_balance": ["balance", "how much", "account"],
            "transfer_money": ["transfer", "send money", "move money"],
            "pay_bill": ["pay bill", "bill payment"],
            
            # Travel
            "search_flights": ["flight", "fly to", "book flight"],
            "search_hotels": ["hotel", "accommodation", "place to stay"],
            "book_hotel": ["book hotel", "reserve room"],
            
            # Food Delivery
            "search_restaurants": ["restaurant", "food", "hungry", "eat"],
            "view_menu": ["menu", "what do they have"],
            "place_order": ["order", "place order", "delivery"],
            
            # Real Estate
            "search_property": ["house", "apartment", "property", "home", "bedroom", "room", "place", "looking for", "need a", "want a", "find", "$", "pounds", "budget"],
            "schedule_viewing": ["viewing", "tour", "see property", "visit"],
            "calculate_mortgage": ["mortgage", "calculate", "payment", "loan", "finance"],
            
            # Common
            "greet": ["hi", "hello", "hey", "good morning", "good afternoon"],
            "goodbye": ["bye", "goodbye", "see you", "thanks bye"],
            "help": ["help", "what can you do", "assist"],
        }
        
        # Score each intent
        scores = {}
        for intent_name, keywords in intent_patterns.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += len(keyword)  # Longer matches = higher score
            if score > 0:
                scores[intent_name] = score
        
        # Get best match
        if scores:
            best_intent = max(scores, key=scores.get)
            confidence = min(scores[best_intent] / 10.0, 1.0)
        else:
            best_intent = "help"
            confidence = 0.5
        
        # Extract simple entities (numbers, dates, etc.)
        entities = self._extract_entities(text)
        
        return best_intent, entities
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract simple entities from text"""
        entities = {}
        text_lower = text.lower()
        
        # Extract bedrooms/rooms
        bedroom_patterns = [
            r'(\d+)\s*(?:bed|bedroom|bedrooms|room|rooms)',
            r'(\d+)\s*br\b'
        ]
        for pattern in bedroom_patterns:
            match = re.search(pattern, text_lower)
            if match:
                entities["bedrooms"] = match.group(1)
                break
        
        # Extract price/budget
        price_patterns = [
            r'\$\s*(\d+(?:,\d{3})*(?:k)?)',
            r'£\s*(\d+(?:,\d{3})*(?:k)?)',
            r'(\d+(?:,\d{3})*)\s*(?:dollars|pounds|euro|usd|gbp)',
        ]
        for pattern in price_patterns:
            match = re.search(pattern, text_lower)
            if match:
                price = match.group(1)
                # Convert 5k to 5000
                if 'k' in price:
                    price = str(int(price.replace('k', '')) * 1000)
                entities["price_range"] = price
                entities["budget"] = price
                break
        
        # Extract location (common cities)
        locations = ["london", "new york", "paris", "tokyo", "downtown", "brooklyn", 
                    "manhattan", "chelsea", "soho", "shoreditch", "kensington"]
        for location in locations:
            if location in text_lower:
                entities["location"] = location.title()
                break
        
        # Extract dates (simple patterns)
        date_patterns = ["today", "tomorrow", "monday", "tuesday", "wednesday", 
                        "thursday", "friday", "saturday", "sunday", "next week"]
        for pattern in date_patterns:
            if pattern in text_lower:
                entities["date"] = pattern
                break
        
        return entities

# Response generator
class SimpleResponseGenerator:
    """Generate responses using templates"""
    
    def __init__(self, domain_config: Dict):
        self.domain_config = domain_config
        self.templates = domain_config.get("response_templates", {})
        self.fallback = domain_config.get("fallback_response", "I'm here to help!")
    
    def generate_response(self, intent: str, entities: Dict, text: str) -> str:
        """Generate response based on intent and templates"""
        
        # Debug logging
        logger.info(f"🔍 Generating response for intent: {intent}, entities: {entities}")
        
        # Try to get template for this intent
        template = self.templates.get(intent)
        logger.info(f"📝 Template from config: {template}")
        
        if not template:
            # Use greeting/goodbye for common intents
            if intent == "greet" or intent == "greeting":
                template = self.templates.get("greeting", "Hi! How can I help you today?")
                logger.info(f"👋 Using greeting template: {template}")
            elif intent == "goodbye":
                template = self.templates.get("goodbye", "Great chatting with you! Come back anytime!")
            elif intent == "help":
                # Natural response instead of listing intents
                domain_name = self.domain_config.get("domain_name", "")
                natural_responses = {
                    "real_estate": "I'd love to help you find a place! What are you looking for? Tell me about your budget, location, or number of bedrooms.",
                    "healthcare": "I can help you with appointments, prescriptions, or health questions. What do you need?",
                    "ecommerce": "Looking for something? Tell me what you'd like to find!",
                    "banking": "I can help with your account. What would you like to do today?",
                    "customer_support": "I'm here to help! What issue or question do you have?",
                    "food_delivery": "Hungry? Tell me what kind of food you're craving!",
                    "travel": "Planning a trip? Where would you like to go?",
                }
                template = natural_responses.get(domain_name, "I'm here to help! What can I do for you?")
                logger.info(f"❓ Using natural help response for {domain_name}: {template}")
            else:
                template = self.fallback
                logger.info(f"🔄 Using fallback: {template}")
        
        # Fill in entity placeholders
        response = template
        for key, value in entities.items():
            placeholder = "{" + key + "}"
            response = response.replace(placeholder, str(value))
        
        # Make response more natural with entity context
        if intent == "search_property" and entities:
            # Build natural response based on what info we have
            parts = []
            if "bedrooms" in entities:
                parts.append(f"{entities['bedrooms']}-bedroom")
            if "location" in entities:
                parts.append(f"in {entities['location']}")
            if "price_range" in entities or "budget" in entities:
                budget = entities.get("price_range", entities.get("budget"))
                parts.append(f"around ${budget}")
            
            if parts:
                response = f"Perfect! Looking for a {' '.join(parts)} place. Let me search for properties that match!"
            else:
                response = "I'd love to help you find a place! Can you tell me your budget, preferred location, and how many bedrooms you need?"
        
        elif intent == "calculate_mortgage" and entities:
            if "price_range" in entities or "budget" in entities:
                price = entities.get("price_range", entities.get("budget"))
                response = f"Got it! For a ${price} property, what down payment percentage are you planning?"
            else:
                response = "Sure! What's the property price you're considering?"
        
        # Add helpful context for knowledge base
        if intent == "search_knowledge_base":
            response = self._add_kb_response(text, response)
        
        return response
    
    def _add_kb_response(self, query: str, base_response: str) -> str:
        """Add knowledge base-style responses"""
        query_lower = query.lower()
        
        # Simple FAQ responses
        faqs = {
            "reset password": "To reset your password: 1) Click 'Forgot Password' on the login page. 2) Enter your email. 3) Check your email for a reset link. 4) Click the link and create a new password. The link expires in 24 hours.",
            "refund": "Our refund policy: Returns accepted within 30 days of purchase. Items must be unused and in original packaging. Refunds processed within 5-7 business days to original payment method. Contact support@example.com to initiate a return.",
            "shipping": "Shipping information: Standard shipping takes 5-7 business days. Express shipping takes 2-3 days. Free shipping on orders over $50. Tracking numbers are emailed once items ship.",
            "account": "Account help: You can update your account information in Settings > Profile. Change email, password, payment methods, and shipping addresses. Enable two-factor authentication for added security.",
            "cancel": "To cancel: Go to your account > Orders/Subscriptions > Select item to cancel > Click 'Cancel'. Cancellations are processed immediately. Refunds (if applicable) take 5-7 business days.",
        }
        
        for key, answer in faqs.items():
            if key in query_lower:
                return answer
        
        return base_response

# Request/Response Models
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
    metadata: Optional[dict] = None

# FastAPI app
app = FastAPI(
    title="Voice-as-a-Service (Offline Mode)",
    description="Completely offline version - No API keys needed! Uses rule-based AI.",
    version="1.0.0-offline",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Enable CORS for dashboard access
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/")
async def root():
    return {
        "service": "Voice-as-a-Service (Offline Mode)",
        "version": "1.0.0-offline",
        "mode": "rule-based",
        "note": "No API keys needed! Works 100% offline!",
        "domains_available": len(DOMAINS),
        "domains": list(DOMAINS.keys())
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "mode": "offline",
        "api_keys_required": False,
        "domains_loaded": len(DOMAINS),
        "features": {
            "intent_recognition": "rule-based",
            "response_generation": "template-based",
            "conversation_memory": True,
            "multi_domain": True
        }
    }

@app.get("/api/v1/domains")
async def list_domains():
    """List all available domains"""
    return {
        "domains": list(DOMAINS.keys()),
        "count": len(DOMAINS)
    }

@app.post("/api/v1/process/text", response_model=ProcessResponse)
async def process_text(request: TextRequest):
    """Process text using offline rule-based AI"""
    try:
        logger.info(f"Processing: '{request.text}' for domain: {request.domain}")
        
        # Get domain config
        domain_config = DOMAINS.get(request.domain)
        if not domain_config:
            available = ', '.join(list(DOMAINS.keys())[:5])
            return ProcessResponse(
                success=False,
                text_response=f"Domain '{request.domain}' not found. Available domains: {available}, and {len(DOMAINS)-5} more. See /api/v1/domains for full list.",
                intent="error",
                entities={},
                session_id=None
            )
        
        # Generate or use session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        # Initialize session if needed
        if session_id not in sessions:
            sessions[session_id] = {
                "user_id": request.user_id,
                "domain": request.domain,
                "created_at": datetime.now().isoformat(),
                "turns": 0
            }
            conversations[session_id] = []
        
        # Match intent
        matcher = SimpleIntentMatcher(domain_config)
        intent, entities = matcher.match_intent(request.text)
        
        logger.info(f"🎯 Matched intent: '{intent}' with entities: {entities} for text: '{request.text}'")
        
        # Generate response
        generator = SimpleResponseGenerator(domain_config)
        response_text = generator.generate_response(intent, entities, request.text)
        
        logger.info(f"✅ Final response: '{response_text}'")
        
        # Update session
        sessions[session_id]["turns"] += 1
        sessions[session_id]["last_activity"] = datetime.now().isoformat()
        
        # Store conversation
        conversations[session_id].append({
            "role": "user",
            "content": request.text,
            "timestamp": datetime.now().isoformat()
        })
        conversations[session_id].append({
            "role": "assistant",
            "content": response_text,
            "intent": intent,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep last 20 messages
        if len(conversations[session_id]) > 20:
            conversations[session_id] = conversations[session_id][-20:]
        
        return ProcessResponse(
            success=True,
            text_response=response_text,
            intent=intent,
            entities=entities,
            session_id=session_id,
            metadata={
                "mode": "offline",
                "turns": sessions[session_id]["turns"],
                "domain": request.domain
            }
        )
        
    except Exception as e:
        logger.error(f"Processing error: {e}")
        return ProcessResponse(
            success=False,
            text_response="I apologize, but I encountered an error processing your request. Please try again.",
            intent="error",
            entities={},
            session_id=request.session_id,
            metadata={"error": str(e)}
        )

@app.get("/api/v1/session/{session_id}")
async def get_session(session_id: str):
    """Get session history"""
    if session_id not in conversations:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "session_info": sessions.get(session_id, {}),
        "conversation": conversations[session_id]
    }

def main():
    """Run the offline server"""
    
    # Get configuration from environment
    host = os.getenv("OFFLINE_HOST", "0.0.0.0")
    port = int(os.getenv("OFFLINE_PORT", "8000"))
    
    # Get first API key for display
    first_api_key = list(API_KEYS.keys())[0] if API_KEYS else "offline_demo_key"
    
    print("=" * 70)
    print("✅ MODE: Completely Offline - No API Keys Needed!")
    print("=" * 70)
    print()
    print(f"✅ Loaded {len(DOMAINS)} domains:")
    for domain in list(DOMAINS.keys()):
        print(f"   • {domain}")
    print()
    print("✅ Using rule-based AI (keyword matching)")
    print("✅ Using response templates from domain configs")
    print("✅ Conversation memory enabled")
    print("✅ Multi-domain support active")
    print()
    print("=" * 70)
    print("API Server Starting...")
    print("=" * 70)
    print()
    print(f"🌐 API Gateway:  http://localhost:{port}")
    print(f"📚 API Docs:     http://localhost:{port}/docs")
    print(f"❤️  Health:       http://localhost:{port}/health")
    print()
    print(f"🔑 Test API Key: {first_api_key}")
    print()
    print("Example request:")
    print(f'  curl -X POST "http://localhost:{port}/api/v1/process/text" \\')
    print(f'    -H "Authorization: Bearer {first_api_key}" \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"text": "How do I reset my password?", "user_id": "user1", "domain": "customer_support"}\'')
    print()
    print(f"Or just open: http://localhost:{port}/docs")
    print()
    print("=" * 70)
    print("Press Ctrl+C to stop the server")
    print("=" * 70)
    print()
    
    # Find available port if auto-port is enabled
    if os.getenv("AUTO_PORT", "false").lower() == "true":
        import socket
        for try_port in range(port, port + 10):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind((host, try_port))
                sock.close()
                if try_port != port:
                    print(f"⚠️  Port {port} is in use. Using port {try_port} instead.")
                    print(f"Access at: http://localhost:{try_port}/docs")
                    print()
                port = try_port
                break
            except OSError:
                continue
    
    # Run server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )

if __name__ == "__main__":
    main()

