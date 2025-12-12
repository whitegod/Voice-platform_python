"""
Load Sample Knowledge Base Data
Populates Qdrant with sample context for RAG
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.data_layer import QdrantVectorDB

load_dotenv()


# Sample real estate knowledge
REAL_ESTATE_DATA = [
    "When buying a home, typical closing costs range from 2-5% of the purchase price.",
    "A home inspection is highly recommended before purchasing and costs $300-500 on average.",
    "Most conventional loans require a 20% down payment to avoid PMI insurance.",
    "Property taxes vary by location but typically range from 0.5% to 2% of home value annually.",
    "HOA fees can range from $100 to $1000+ per month depending on the community amenities.",
    "The mortgage pre-approval process typically takes 3-10 business days.",
    "First-time homebuyers may qualify for FHA loans with as little as 3.5% down.",
    "A good credit score for mortgage approval is typically 620 or higher.",
    "Real estate agents typically charge 5-6% commission, split between buyer and seller agents.",
    "The home buying process from offer to closing typically takes 30-45 days.",
]

# Sample food delivery knowledge
FOOD_DELIVERY_DATA = [
    "Delivery fees typically range from $2 to $10 depending on distance and demand.",
    "Most restaurants have a minimum order amount of $10-15 for delivery.",
    "Peak hours (lunch 11am-2pm and dinner 6pm-9pm) may have higher delivery fees.",
    "You can track your driver in real-time through the app once food is picked up.",
    "Contactless delivery is available - instructions can be added in delivery notes.",
    "Most orders arrive within 30-60 minutes depending on restaurant preparation time.",
    "You can schedule orders up to 7 days in advance for future delivery.",
    "Tips are separate from delivery fees and typically range from 15-20%.",
    "If your order is incorrect or missing items, contact support for a refund or redelivery.",
    "Many restaurants offer exclusive discounts when ordering through delivery apps.",
]


async def main():
    """Load sample data into Qdrant"""
    print("Loading sample knowledge base data...")
    
    try:
        # Initialize Qdrant
        qdrant = QdrantVectorDB(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
            collection_name="vaas_embeddings"
        )
        
        # Create collections
        print("\nCreating vector collections...")
        
        await qdrant.create_collection("real_estate_knowledge")
        await qdrant.create_collection("food_delivery_knowledge")
        
        # Load real estate data
        print("\nLoading real estate knowledge...")
        metadata = [{"category": "real_estate", "source": "sample"} 
                   for _ in REAL_ESTATE_DATA]
        
        await qdrant.insert(
            texts=REAL_ESTATE_DATA,
            metadata=metadata,
            collection_name="real_estate_knowledge",
            tenant_id="demo_tenant"
        )
        
        # Load food delivery data
        print("Loading food delivery knowledge...")
        metadata = [{"category": "food_delivery", "source": "sample"} 
                   for _ in FOOD_DELIVERY_DATA]
        
        await qdrant.insert(
            texts=FOOD_DELIVERY_DATA,
            metadata=metadata,
            collection_name="food_delivery_knowledge",
            tenant_id="demo_tenant"
        )
        
        print("\n✅ Sample data loaded successfully!")
        
        # Test search
        print("\nTesting search...")
        results = await qdrant.search(
            "What are typical closing costs?",
            collection_name="real_estate_knowledge",
            tenant_id="demo_tenant",
            limit=3
        )
        
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['text'][:100]}... (score: {result['score']:.3f})")
        
    except Exception as e:
        print(f"❌ Failed to load data: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

