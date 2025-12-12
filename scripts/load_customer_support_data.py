#!/usr/bin/env python3
"""
Load Customer Support Knowledge Base
Populates Qdrant with support documentation and FAQs
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.data_layer import QdrantVectorDB

load_dotenv()


# Customer Support Knowledge Base
SUPPORT_KNOWLEDGE = [
    # Account Management
    "To reset your password, click 'Forgot Password' on the login page and follow the email instructions.",
    "You can update your email address in Account Settings > Profile > Contact Information.",
    "Two-factor authentication can be enabled in Security Settings for added account protection.",
    "To close your account, go to Settings > Account > Delete Account. This action is permanent.",
    "Free accounts include basic features. Premium plans start at $9.99/month with advanced features.",
    
    # Billing & Payments
    "We accept Visa, MasterCard, American Express, and PayPal for payments.",
    "Billing occurs on the same date each month. You'll receive an invoice 3 days before charging.",
    "Refunds are processed within 5-7 business days to the original payment method.",
    "You can cancel your subscription anytime. Access continues until the end of the billing period.",
    "Pro-rated refunds are available if you downgrade within 14 days of upgrading.",
    
    # Technical Support
    "Clear your browser cache if experiencing loading issues: Ctrl+Shift+Delete (Cmd+Shift+Delete on Mac).",
    "Supported browsers: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+. Update for best performance.",
    "If the app crashes, try reinstalling. Your data is safely stored in the cloud.",
    "API rate limits: Free tier 100 requests/hour, Premium 1000/hour, Enterprise unlimited.",
    "For connection errors, check your internet connection and firewall settings.",
    
    # Features & Usage
    "Upload files up to 100MB. Supported formats: PDF, DOCX, XLSX, JPG, PNG, MP4.",
    "Shared links expire after 7 days by default. This can be customized in sharing settings.",
    "Dark mode is available in Appearance Settings. It automatically activates at sunset.",
    "Keyboard shortcuts: Ctrl+S to save, Ctrl+Z to undo, Ctrl+F to search.",
    "Export your data anytime from Settings > Data & Privacy > Export All Data.",
    
    # Shipping & Delivery
    "Standard shipping takes 5-7 business days. Express shipping delivers in 2-3 days.",
    "Free shipping on orders over $50. Tracking numbers are emailed once shipped.",
    "International shipping available to 50+ countries. Customs fees may apply.",
    "Signature required for orders over $200 for security purposes.",
    
    # Returns & Refunds
    "Return items within 30 days for a full refund. Items must be unused and in original packaging.",
    "Digital products are non-refundable unless they're defective or don't match description.",
    "Return shipping is free. We'll email you a prepaid return label.",
    "Refunds appear in your account within 5-7 business days after we receive the return.",
    
    # Security & Privacy
    "We use 256-bit SSL encryption to protect your data during transmission.",
    "Your data is backed up daily and stored in secure, redundant data centers.",
    "We never sell your personal information. See our Privacy Policy for details.",
    "Two-factor authentication adds an extra security layer using SMS or authenticator apps.",
    "Report security concerns immediately to security@example.com.",
    
    # Troubleshooting
    "Error 500: Our servers are having issues. Try again in a few minutes or contact support.",
    "Error 401: Your session expired. Please log in again to continue.",
    "Error 403: You don't have permission for this action. Contact your admin.",
    "Error 404: The page doesn't exist. Check the URL or use our search function.",
    "If payment fails, verify card details, expiration date, and billing address match.",
    
    # Mobile App
    "The mobile app is available on iOS 13+ and Android 8+. Download from App Store or Google Play.",
    "Enable push notifications in app settings to receive real-time updates.",
    "Offline mode lets you access recent content without internet. Syncs when reconnected.",
    "App storage: iOS users can manage in Settings > General > iPhone Storage.",
    
    # Integrations
    "Integrate with Slack, Microsoft Teams, Google Workspace, and 50+ other apps.",
    "API documentation available at docs.example.com/api with code examples.",
    "Webhooks notify your systems of events in real-time. Configure in Developer Settings.",
    "Zapier integration available for no-code automation with 3000+ apps.",
    
    # Business & Enterprise
    "Enterprise plans include dedicated support, custom integrations, and SLA guarantees.",
    "Volume discounts available for teams of 50+ users. Contact sales@example.com.",
    "SSO (Single Sign-On) available with SAML 2.0 for Enterprise plans.",
    "Compliance: We're SOC 2, GDPR, and HIPAA compliant. Audit reports available on request.",
    
    # General Policies
    "Business hours: Support available 24/7. Live chat 9am-5pm ET, email anytime.",
    "Average response time: Live chat 2 minutes, email 2 hours, phone immediate.",
    "Service Level Agreement: 99.9% uptime guarantee for Premium and Enterprise plans.",
    "Terms of Service and Privacy Policy available at example.com/legal.",
]


async def main():
    """Load customer support knowledge base"""
    print("Loading Customer Support Knowledge Base...")
    print("=" * 70)
    
    try:
        # Initialize Qdrant
        qdrant = QdrantVectorDB(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
            collection_name="customer_support_kb"
        )
        
        # Create collection
        print("\n1. Creating vector collection...")
        await qdrant.create_collection("customer_support_kb")
        print("   ✓ Collection created")
        
        # Prepare metadata
        metadata = []
        for item in SUPPORT_KNOWLEDGE:
            # Categorize based on content
            if any(word in item.lower() for word in ['password', 'account', 'login', 'security']):
                category = "account_security"
            elif any(word in item.lower() for word in ['billing', 'payment', 'refund', 'subscription']):
                category = "billing"
            elif any(word in item.lower() for word in ['error', 'crash', 'browser', 'technical']):
                category = "technical"
            elif any(word in item.lower() for word in ['shipping', 'delivery', 'return']):
                category = "shipping"
            elif any(word in item.lower() for word in ['api', 'integration', 'webhook']):
                category = "integrations"
            else:
                category = "general"
            
            metadata.append({
                "category": category,
                "source": "support_kb",
                "type": "faq"
            })
        
        # Load knowledge
        print(f"\n2. Loading {len(SUPPORT_KNOWLEDGE)} knowledge items...")
        await qdrant.insert(
            texts=SUPPORT_KNOWLEDGE,
            metadata=metadata,
            collection_name="customer_support_kb",
            tenant_id="demo_tenant"
        )
        print(f"   ✓ Loaded {len(SUPPORT_KNOWLEDGE)} items")
        
        # Test search
        print("\n3. Testing search functionality...")
        test_queries = [
            "How do I reset my password?",
            "What's your refund policy?",
            "My payment failed, what should I do?"
        ]
        
        for query in test_queries:
            results = await qdrant.search(
                query=query,
                collection_name="customer_support_kb",
                tenant_id="demo_tenant",
                limit=3
            )
            print(f"\n   Query: '{query}'")
            print(f"   Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"     {i}. [{result['metadata']['category']}] {result['text'][:80]}...")
                print(f"        (score: {result['score']:.3f})")
        
        print("\n" + "=" * 70)
        print("✅ Customer Support knowledge base loaded successfully!")
        print("\nYou can now use the 'customer_support' domain with RAG-enhanced responses.")
        print("\nTest it:")
        print('  curl -X POST "http://localhost:8000/api/v1/process/text" \\')
        print('    -H "Authorization: Bearer YOUR_API_KEY" \\')
        print('    -H "Content-Type: application/json" \\')
        print('    -d \'{"text": "How do I reset my password?", "user_id": "test", "domain": "customer_support"}\'')
        print()
        
    except Exception as e:
        print(f"\n❌ Failed to load knowledge base: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())

