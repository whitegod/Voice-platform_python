#!/usr/bin/env python3
"""
Load All Knowledge Bases
Populates Qdrant with knowledge for all domains
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.data_layer import QdrantVectorDB

load_dotenv()

# Colors
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

# Knowledge bases for all domains
KNOWLEDGE_BASES = {
    "customer_support_kb": [
        # Account & Security
        "To reset your password, click 'Forgot Password' on the login page and follow the email instructions.",
        "You can update your email address in Account Settings > Profile > Contact Information.",
        "Two-factor authentication can be enabled in Security Settings for added account protection.",
        "To close your account, go to Settings > Account > Delete Account. This action is permanent.",
        
        # Billing & Payments
        "We accept Visa, MasterCard, American Express, and PayPal for payments.",
        "Billing occurs on the same date each month. You'll receive an invoice 3 days before charging.",
        "Refunds are processed within 5-7 business days to the original payment method.",
        "You can cancel your subscription anytime. Access continues until the end of the billing period.",
        
        # Technical Support
        "Clear your browser cache if experiencing loading issues: Ctrl+Shift+Delete.",
        "Supported browsers: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+.",
        "If the app crashes, try reinstalling. Your data is safely stored in the cloud.",
        "API rate limits: Free tier 100 requests/hour, Premium 1000/hour, Enterprise unlimited.",
    ],
    
    "healthcare_knowledge": [
        "Regular checkups are recommended annually for adults.",
        "Most insurance plans cover preventive care at no cost.",
        "Bring your insurance card and ID to your first appointment.",
        "Arrive 15 minutes early to complete registration forms.",
        "You can cancel appointments up to 24 hours in advance without penalty.",
        "Telemedicine visits are available for non-emergency consultations.",
        "Prescription refills can be requested online through the patient portal.",
        "Lab results are typically available within 2-3 business days.",
        "For emergencies, always call 911 or go to the nearest emergency room.",
        "Urgent care is appropriate for minor injuries and illnesses that need prompt attention.",
    ],
    
    "real_estate_knowledge": [
        "Typical closing costs range from 2-5% of the purchase price.",
        "A home inspection costs $300-500 and is highly recommended before purchasing.",
        "Most conventional loans require a 20% down payment to avoid PMI insurance.",
        "Property taxes typically range from 0.5% to 2% of home value annually.",
        "HOA fees can range from $100 to $1000+ per month depending on amenities.",
        "Mortgage pre-approval typically takes 3-10 business days.",
        "First-time homebuyers may qualify for FHA loans with 3.5% down.",
        "A good credit score for mortgage approval is typically 620 or higher.",
        "Real estate agents typically charge 5-6% commission split between agents.",
        "The home buying process from offer to closing takes 30-45 days.",
    ],
    
    "food_delivery_knowledge": [
        "Delivery fees typically range from $2 to $10 depending on distance.",
        "Most restaurants have a minimum order amount of $10-15 for delivery.",
        "Peak hours (lunch 11am-2pm, dinner 6pm-9pm) may have higher fees.",
        "You can track your driver in real-time once food is picked up.",
        "Contactless delivery is available - add instructions in delivery notes.",
        "Most orders arrive within 30-60 minutes depending on preparation time.",
        "You can schedule orders up to 7 days in advance.",
        "Tips are separate from delivery fees and typically range from 15-20%.",
        "If your order is incorrect, contact support immediately for refund or redelivery.",
        "Many restaurants offer exclusive discounts through delivery apps.",
    ],
    
    "ecommerce_knowledge": [
        "Free shipping is available on orders over $50.",
        "Returns are accepted within 30 days with original packaging.",
        "Order tracking numbers are emailed once items ship.",
        "Standard shipping takes 5-7 business days, express is 2-3 days.",
        "International shipping available to 50+ countries with customs fees.",
        "Price match guarantee if you find it cheaper elsewhere.",
        "Student and military discounts available with verification.",
        "Gift cards never expire and can be used on any product.",
        "Save items to wishlist to get notified of price drops.",
        "Customer service available 24/7 via chat, phone, or email.",
    ],
    
    "banking_knowledge": [
        "ATMs are fee-free for account holders at 50,000+ locations nationwide.",
        "Mobile check deposit available for checks under $5,000.",
        "Direct deposit typically posts 2 days earlier than paper checks.",
        "Overdraft protection links savings to checking to prevent fees.",
        "Wire transfers are processed same-day for domestic, 1-3 days international.",
        "Credit score updates are available monthly to all account holders.",
        "Bill pay service allows scheduled automatic payments.",
        "FDIC insurance protects deposits up to $250,000 per account.",
        "Lost or stolen cards can be replaced in 5-7 business days.",
        "Online banking uses 256-bit encryption for security.",
    ],
    
    "fitness_knowledge": [
        "Beginners should start with 3 workouts per week, 30 minutes each.",
        "Rest days are essential for muscle recovery and growth.",
        "Proper form is more important than lifting heavy weights.",
        "Stay hydrated - drink water before, during, and after workouts.",
        "Warm up for 5-10 minutes before exercise to prevent injury.",
        "Protein intake should be 0.8-1g per pound of body weight for muscle building.",
        "Cardio is effective for heart health and fat loss.",
        "Consistency is key - small progress daily beats sporadic intense workouts.",
        "Track your progress with photos, measurements, or workout logs.",
        "Consult a doctor before starting any new fitness program.",
    ],
    
    "personal_finance_knowledge": [
        "The 50/30/20 rule: 50% needs, 30% wants, 20% savings.",
        "Emergency fund should cover 3-6 months of expenses.",
        "Pay off high-interest debt before investing.",
        "Start retirement savings early - compound interest is powerful.",
        "Track every expense for at least one month to understand spending.",
        "Automate savings transfers to make it effortless.",
        "Credit card rewards are only beneficial if you pay in full monthly.",
        "Review subscriptions quarterly and cancel unused services.",
        "Negotiate bills like insurance, internet, and phone regularly.",
        "Diversification reduces investment risk.",
    ],
}


async def load_knowledge_base(qdrant, collection_name, knowledge_items, tenant_id="demo_tenant"):
    """Load a specific knowledge base"""
    try:
        print(f"\n  Loading {collection_name}...")
        print(f"    Items: {len(knowledge_items)}")
        
        # Create collection
        await qdrant.create_collection(collection_name)
        print(f"    ✓ Collection created/verified")
        
        # Prepare metadata
        metadata = [{"source": collection_name, "type": "faq"} 
                   for _ in knowledge_items]
        
        # Insert knowledge
        await qdrant.insert(
            texts=knowledge_items,
            metadata=metadata,
            collection_name=collection_name,
            tenant_id=tenant_id
        )
        
        print(f"    ✓ {len(knowledge_items)} items loaded")
        
        # Test search
        test_query = knowledge_items[0][:30]  # Use first 30 chars as test
        results = await qdrant.search(
            query=test_query,
            collection_name=collection_name,
            tenant_id=tenant_id,
            limit=3
        )
        
        print(f"    ✓ Search test: {len(results)} results found")
        
        return True, len(knowledge_items)
        
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False, 0


async def main():
    """Load all knowledge bases"""
    print(f"{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}Loading All Knowledge Bases into Qdrant{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}")
    
    # Initialize Qdrant
    print(f"\n{Colors.BLUE}Initializing Qdrant client...{Colors.END}")
    try:
        qdrant = QdrantVectorDB(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
            collection_name="default"
        )
        print(f"{Colors.GREEN}✓ Qdrant client initialized{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}✗ Failed to initialize Qdrant: {e}{Colors.END}")
        return 1
    
    # Health check
    try:
        healthy = await qdrant.health_check()
        if healthy:
            print(f"{Colors.GREEN}✓ Qdrant is healthy{Colors.END}")
        else:
            print(f"{Colors.RED}✗ Qdrant health check failed{Colors.END}")
            return 1
    except Exception as e:
        print(f"{Colors.RED}✗ Cannot connect to Qdrant: {e}{Colors.END}")
        print(f"\n{Colors.YELLOW}Make sure Qdrant is running:{Colors.END}")
        print("  docker-compose up -d qdrant")
        return 1
    
    # Load each knowledge base
    print(f"\n{Colors.BOLD}Loading knowledge bases:{Colors.END}")
    
    total_loaded = 0
    successful = 0
    failed = 0
    
    for collection_name, knowledge_items in KNOWLEDGE_BASES.items():
        success, count = await load_knowledge_base(
            qdrant, 
            collection_name, 
            knowledge_items
        )
        
        if success:
            successful += 1
            total_loaded += count
        else:
            failed += 1
    
    # Summary
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}Summary{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"\n{Colors.GREEN}✓ Successful: {successful}/{len(KNOWLEDGE_BASES)} collections{Colors.END}")
    if failed > 0:
        print(f"{Colors.RED}✗ Failed: {failed}/{len(KNOWLEDGE_BASES)} collections{Colors.END}")
    print(f"{Colors.BLUE}ℹ Total items loaded: {total_loaded}{Colors.END}")
    
    # List collections
    print(f"\n{Colors.BOLD}Available collections:{Colors.END}")
    for collection_name in KNOWLEDGE_BASES.keys():
        print(f"  • {collection_name}")
    
    print(f"\n{Colors.GREEN}{'='*70}{Colors.END}")
    print(f"{Colors.GREEN}✅ Knowledge Base Loading Complete!{Colors.END}")
    print(f"{Colors.GREEN}{'='*70}{Colors.END}")
    
    print(f"\n{Colors.BOLD}Test your knowledge bases:{Colors.END}")
    print('  curl -X POST "http://localhost:8000/api/v1/process/text" \\')
    print('    -H "Authorization: Bearer YOUR_API_KEY" \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"text": "How do I reset my password?", "user_id": "test", "domain": "customer_support"}\'')
    print()
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

