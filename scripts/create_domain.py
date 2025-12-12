#!/usr/bin/env python3
"""
Domain Creation Wizard
Interactive tool to create new domain configurations
"""

import json
from pathlib import Path
from typing import List, Dict


def create_domain_wizard():
    """Interactive domain creation wizard"""
    print("=" * 70)
    print("VaaS Domain Creation Wizard")
    print("=" * 70)
    print("\nThis wizard will help you create a new domain configuration.\n")
    
    # Basic Information
    print("--- Basic Information ---")
    domain_name = input("Domain name (e.g., healthcare, retail): ").strip().lower().replace(" ", "_")
    description = input("Brief description: ").strip()
    print()
    
    # System Prompt
    print("--- AI Assistant Configuration ---")
    print("Define how the AI should behave:")
    assistant_role = input("Assistant role (e.g., healthcare assistant, shopping helper): ").strip()
    tone = input("Tone (e.g., professional, friendly, casual): ").strip()
    
    system_prompt = f"You are a helpful {assistant_role}. Use a {tone} tone. "
    system_prompt += input("Additional instructions (optional): ").strip()
    print()
    
    # Intents
    print("--- Intents Configuration ---")
    print("Define what users can ask for (e.g., search_products, book_appointment)")
    intents = []
    
    while True:
        intent_name = input("\nIntent name (or 'done' to finish): ").strip()
        if intent_name.lower() == 'done':
            break
        
        # Entities
        print(f"  What information do you need for '{intent_name}'?")
        print("  (e.g., product_name, date, location)")
        entities_str = input("  Entities (comma-separated): ").strip()
        entities = [e.strip() for e in entities_str.split(",") if e.strip()]
        
        # API Configuration
        has_api = input("  Does this connect to an external API? (y/N): ").lower() == 'y'
        
        intent_config = {
            "name": intent_name,
            "entities": entities,
            "api_endpoint": None,
            "api_method": "POST",
            "api_headers": {"Content-Type": "application/json"},
            "response_template": None,
            "requires_auth": False
        }
        
        if has_api:
            api_endpoint = input("  API endpoint URL: ").strip()
            api_method = input("  HTTP method (GET/POST/PUT/DELETE) [POST]: ").strip().upper() or "POST"
            requires_auth = input("  Requires authentication? (y/N): ").lower() == 'y'
            
            intent_config["api_endpoint"] = api_endpoint
            intent_config["api_method"] = api_method
            intent_config["requires_auth"] = requires_auth
        
        # Response Template
        print("  Response template (use {variable_name} for placeholders):")
        response_template = input("  > ").strip()
        intent_config["response_template"] = response_template
        
        intents.append(intent_config)
        print(f"  ✓ Added intent: {intent_name}")
    
    if not intents:
        print("\n⚠️  No intents defined! Adding a default example intent.")
        intents.append({
            "name": "help",
            "entities": [],
            "api_endpoint": None,
            "api_method": "GET",
            "api_headers": {"Content-Type": "application/json"},
            "response_template": "I can help you with various tasks. What would you like to do?",
            "requires_auth": False
        })
    
    print()
    
    # Context Retrieval (RAG)
    print("--- Knowledge Base Configuration ---")
    enable_rag = input("Enable context retrieval (RAG)? (Y/n): ").lower() != 'n'
    
    context_retrieval = {
        "enabled": enable_rag,
        "collection_name": f"{domain_name}_knowledge" if enable_rag else None,
        "top_k": 5 if enable_rag else 0,
        "score_threshold": 0.6 if enable_rag else 0
    }
    
    if enable_rag:
        top_k = input("Number of context items to retrieve [5]: ").strip()
        context_retrieval["top_k"] = int(top_k) if top_k else 5
    
    print()
    
    # Response Templates
    print("--- Response Templates ---")
    response_templates = {}
    
    greeting = input("Greeting message: ").strip()
    if greeting:
        response_templates["greeting"] = greeting
    
    goodbye = input("Goodbye message: ").strip()
    if goodbye:
        response_templates["goodbye"] = goodbye
    
    # Add intent-specific templates
    for intent in intents:
        response_templates[intent["name"]] = intent["response_template"] or f"Processing {intent['name']}..."
    
    # Fallback
    fallback = input("Fallback message (when intent not understood): ").strip()
    if not fallback:
        fallback = "I'm not sure I understand. Could you please rephrase that?"
    
    print()
    
    # Build configuration
    config = {
        "domain_name": domain_name,
        "description": description,
        "system_prompt": system_prompt,
        "intents": intents,
        "context_retrieval": context_retrieval,
        "response_templates": response_templates,
        "fallback_response": fallback,
        "max_turns": 50,
        "metadata": {
            "version": "1.0",
            "created_with": "domain_wizard",
            "contact": "support@example.com"
        }
    }
    
    # Save configuration
    print("--- Saving Configuration ---")
    config_dir = Path("config/domains")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    config_path = config_dir / f"{domain_name}.json"
    
    if config_path.exists():
        overwrite = input(f"{config_path} already exists. Overwrite? (y/N): ").lower()
        if overwrite != 'y':
            print("Cancelled.")
            return
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Domain configuration saved to: {config_path}")
    
    # Generate Rasa training data template
    print("\n--- Generating Rasa Training Data Template ---")
    
    rasa_template = f"\n# {domain_name.title()} Domain\n"
    for intent in intents:
        rasa_template += f"\n- intent: {intent['name']}\n"
        rasa_template += "  examples: |\n"
        rasa_template += f"    - I want to {intent['name'].replace('_', ' ')}\n"
        rasa_template += f"    - Help me with {intent['name'].replace('_', ' ')}\n"
        
        for entity in intent['entities']:
            rasa_template += f"    - {intent['name'].replace('_', ' ')} with [{entity}_value]({entity})\n"
    
    rasa_path = Path("config/rasa") / f"{domain_name}_nlu_template.yml"
    rasa_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(rasa_path, 'w') as f:
        f.write(rasa_template)
    
    print(f"✅ Rasa template saved to: {rasa_path}")
    
    # Knowledge base script template
    if enable_rag:
        print("\n--- Generating Knowledge Base Script Template ---")
        
        kb_script = f'''#!/usr/bin/env python3
"""
Load {domain_name.title()} Knowledge Base
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_layer import QdrantVectorDB

# Add your knowledge items here
KNOWLEDGE_ITEMS = [
    "Example knowledge item 1",
    "Example knowledge item 2",
    "Example knowledge item 3",
    # Add more items...
]

async def main():
    print("Loading {domain_name} knowledge base...")
    
    qdrant = QdrantVectorDB()
    
    # Create collection
    await qdrant.create_collection("{domain_name}_knowledge")
    
    # Insert knowledge
    metadata = [{{"source": "{domain_name}_kb"}} for _ in KNOWLEDGE_ITEMS]
    
    await qdrant.insert(
        texts=KNOWLEDGE_ITEMS,
        metadata=metadata,
        collection_name="{domain_name}_knowledge",
        tenant_id="demo_tenant"
    )
    
    print(f"✅ Loaded {{len(KNOWLEDGE_ITEMS)}} knowledge items")

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        kb_path = Path("scripts") / f"load_{domain_name}_data.py"
        with open(kb_path, 'w') as f:
            f.write(kb_script)
        
        print(f"✅ Knowledge base script saved to: {kb_path}")
    
    # Next Steps
    print("\n" + "=" * 70)
    print("Next Steps:")
    print("=" * 70)
    print(f"\n1. Review and edit the configuration:")
    print(f"   {config_path}")
    print(f"\n2. Add training data to Rasa:")
    print(f"   - Edit config/rasa/nlu.yml")
    print(f"   - Use {rasa_path} as a template")
    print(f"\n3. Update Rasa domain file:")
    print(f"   - Edit config/rasa/domain.yml")
    print(f"   - Add your intents and entities")
    print(f"\n4. Train Rasa model:")
    print(f"   docker-compose exec rasa rasa train")
    print(f"\n5. Load knowledge base (if RAG enabled):")
    if enable_rag:
        print(f"   python scripts/load_{domain_name}_data.py")
    print(f"\n6. Test your domain:")
    print(f'   curl -X POST "http://localhost:8000/api/v1/process/text" \\')
    print(f'     -H "Authorization: Bearer YOUR_API_KEY" \\')
    print(f'     -H "Content-Type: application/json" \\')
    print(f'     -d \'{{"text": "test query", "user_id": "test", "domain": "{domain_name}"}}\'')
    print()
    print("For detailed guidance, see: DOMAIN_CUSTOMIZATION.md")
    print()


if __name__ == "__main__":
    try:
        create_domain_wizard()
    except KeyboardInterrupt:
        print("\n\nWizard cancelled.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

