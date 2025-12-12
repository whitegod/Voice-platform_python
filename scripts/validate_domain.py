#!/usr/bin/env python3
"""
Domain Configuration Validator
Validates domain JSON files for correctness
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def validate_domain_config(config_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate a domain configuration file.
    
    Returns:
        (is_valid, errors)
    """
    errors = []
    
    # Check file exists
    if not config_path.exists():
        return False, [f"File not found: {config_path}"]
    
    # Parse JSON
    try:
        with open(config_path) as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"]
    
    # Required fields
    required_fields = ["domain_name", "intents"]
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Validate domain_name
    if "domain_name" in config:
        domain_name = config["domain_name"]
        if not domain_name or not isinstance(domain_name, str):
            errors.append("domain_name must be a non-empty string")
        elif not domain_name.replace("_", "").isalnum():
            errors.append("domain_name should only contain letters, numbers, and underscores")
    
    # Validate intents
    if "intents" in config:
        intents = config["intents"]
        
        if not isinstance(intents, list):
            errors.append("intents must be an array")
        elif len(intents) == 0:
            errors.append("At least one intent is required")
        else:
            intent_names = set()
            for i, intent in enumerate(intents):
                intent_path = f"intents[{i}]"
                
                # Required intent fields
                if not isinstance(intent, dict):
                    errors.append(f"{intent_path} must be an object")
                    continue
                
                if "name" not in intent:
                    errors.append(f"{intent_path}: Missing required field 'name'")
                else:
                    name = intent["name"]
                    if not name or not isinstance(name, str):
                        errors.append(f"{intent_path}: 'name' must be a non-empty string")
                    elif name in intent_names:
                        errors.append(f"{intent_path}: Duplicate intent name '{name}'")
                    else:
                        intent_names.add(name)
                
                # Validate entities
                if "entities" in intent:
                    if not isinstance(intent["entities"], list):
                        errors.append(f"{intent_path}: 'entities' must be an array")
                
                # Validate API configuration
                if "api_endpoint" in intent:
                    endpoint = intent["api_endpoint"]
                    if endpoint and not isinstance(endpoint, str):
                        errors.append(f"{intent_path}: 'api_endpoint' must be a string")
                    elif endpoint and not (endpoint.startswith("http://") or endpoint.startswith("https://")):
                        errors.append(f"{intent_path}: 'api_endpoint' should be a valid URL")
                
                if "api_method" in intent:
                    method = intent["api_method"]
                    valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
                    if method and method not in valid_methods:
                        errors.append(f"{intent_path}: 'api_method' must be one of {valid_methods}")
                
                if "api_headers" in intent:
                    if not isinstance(intent["api_headers"], dict):
                        errors.append(f"{intent_path}: 'api_headers' must be an object")
    
    # Validate context_retrieval
    if "context_retrieval" in config:
        rag = config["context_retrieval"]
        
        if not isinstance(rag, dict):
            errors.append("context_retrieval must be an object")
        else:
            if "enabled" in rag and not isinstance(rag["enabled"], bool):
                errors.append("context_retrieval.enabled must be a boolean")
            
            if rag.get("enabled"):
                if "collection_name" not in rag or not rag["collection_name"]:
                    errors.append("context_retrieval.collection_name is required when enabled")
                
                if "top_k" in rag:
                    top_k = rag["top_k"]
                    if not isinstance(top_k, int) or top_k < 1:
                        errors.append("context_retrieval.top_k must be a positive integer")
                
                if "score_threshold" in rag:
                    threshold = rag["score_threshold"]
                    if not isinstance(threshold, (int, float)) or not 0 <= threshold <= 1:
                        errors.append("context_retrieval.score_threshold must be between 0 and 1")
    
    # Validate response_templates
    if "response_templates" in config:
        templates = config["response_templates"]
        if not isinstance(templates, dict):
            errors.append("response_templates must be an object")
    
    # Validate max_turns
    if "max_turns" in config:
        max_turns = config["max_turns"]
        if not isinstance(max_turns, int) or max_turns < 1:
            errors.append("max_turns must be a positive integer")
    
    # Validate metadata
    if "metadata" in config:
        if not isinstance(config["metadata"], dict):
            errors.append("metadata must be an object")
    
    return len(errors) == 0, errors


def main():
    """Main validation function"""
    if len(sys.argv) < 2:
        print("Usage: python validate_domain.py <domain_name_or_path>")
        print("\nExamples:")
        print("  python validate_domain.py healthcare")
        print("  python validate_domain.py config/domains/healthcare.json")
        sys.exit(1)
    
    arg = sys.argv[1]
    
    # Determine config path
    if arg.endswith('.json'):
        config_path = Path(arg)
    else:
        config_path = Path("config/domains") / f"{arg}.json"
    
    print(f"Validating domain configuration: {config_path}")
    print("=" * 70)
    
    is_valid, errors = validate_domain_config(config_path)
    
    if is_valid:
        print("✅ Configuration is valid!")
        
        # Load and show summary
        with open(config_path) as f:
            config = json.load(f)
        
        print(f"\nDomain: {config['domain_name']}")
        if "description" in config:
            print(f"Description: {config['description']}")
        print(f"Intents: {len(config['intents'])}")
        for intent in config['intents']:
            entities = ", ".join(intent.get('entities', []))
            has_api = "✓" if intent.get('api_endpoint') else "✗"
            print(f"  - {intent['name']} [{has_api} API] ({entities or 'no entities'})")
        
        if config.get("context_retrieval", {}).get("enabled"):
            print(f"RAG: Enabled (collection: {config['context_retrieval']['collection_name']})")
        else:
            print("RAG: Disabled")
        
        return 0
    else:
        print("❌ Configuration has errors:\n")
        for i, error in enumerate(errors, 1):
            print(f"{i}. {error}")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())

