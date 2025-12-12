#!/usr/bin/env python3
"""
Advanced Rasa Training Script with Progress Tracking
Trains Rasa model and provides detailed feedback
"""

import sys
import os
import subprocess
import time
import json
from pathlib import Path
import requests

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def check_docker():
    """Check if Docker is running"""
    try:
        subprocess.run(["docker", "info"], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
        return True
    except:
        return False

def check_rasa_container():
    """Check if Rasa container is running"""
    try:
        result = subprocess.run(
            ["docker-compose", "ps", "rasa"],
            capture_output=True,
            text=True
        )
        return "Up" in result.stdout
    except:
        return False

def start_rasa():
    """Start Rasa container"""
    print_info("Starting Rasa container...")
    try:
        subprocess.run(["docker-compose", "up", "-d", "rasa"], check=True)
        time.sleep(10)
        return True
    except:
        return False

def merge_nlu_files():
    """Merge domain-specific NLU files into main nlu.yml"""
    print_info("Checking for domain-specific NLU files...")
    
    rasa_dir = Path("config/rasa")
    nlu_files = list(rasa_dir.glob("*_nlu.yml"))
    
    if not nlu_files:
        print_warning("No domain-specific NLU files found")
        return True
    
    print_info(f"Found {len(nlu_files)} domain NLU files")
    
    # Backup main nlu.yml
    main_nlu = rasa_dir / "nlu.yml"
    if main_nlu.exists():
        backup = rasa_dir / "nlu_backup.yml"
        subprocess.run(["cp", str(main_nlu), str(backup)])
        print_info(f"Backed up nlu.yml to {backup}")
    
    # Merge files (in Python to ensure proper YAML handling)
    # For simplicity, we'll append (assuming proper YAML structure)
    for nlu_file in nlu_files:
        print_info(f"  - Processing {nlu_file.name}")
        with open(nlu_file, 'r') as f:
            content = f.read()
        
        # Append to main file (skip version header if present)
        with open(main_nlu, 'a') as f:
            lines = content.split('\n')
            # Skip version line and empty lines at start
            start_idx = 0
            for i, line in enumerate(lines):
                if line.strip() and not line.startswith('version:'):
                    start_idx = i
                    break
            f.write('\n' + '\n'.join(lines[start_idx:]))
    
    print_success("NLU files merged successfully")
    return True

def validate_config():
    """Validate Rasa configuration files"""
    required_files = [
        "config/rasa/nlu.yml",
        "config/rasa/domain.yml",
        "config/rasa/config.yml"
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print_error(f"Required file missing: {file_path}")
            return False
        print_success(f"Found {file_path}")
    
    return True

def train_model():
    """Train the Rasa model"""
    print_info("Starting model training (this may take several minutes)...")
    print_info("Training progress:")
    
    try:
        # Run training command
        result = subprocess.run([
            "docker-compose", "exec", "-T", "rasa",
            "rasa", "train",
            "--config", "/app/config.yml",
            "--domain", "/app/domain.yml",
            "--data", "/app/nlu.yml",
            "--out", "/app/models"
        ], capture_output=True, text=True)
        
        # Show output
        if result.stdout:
            print(result.stdout)
        
        if result.returncode == 0:
            print_success("Model training completed!")
            return True
        else:
            print_error("Training failed")
            if result.stderr:
                print(result.stderr)
            return False
            
    except Exception as e:
        print_error(f"Training error: {e}")
        return False

def restart_rasa():
    """Restart Rasa server"""
    print_info("Restarting Rasa server to load new model...")
    try:
        subprocess.run(["docker-compose", "restart", "rasa"], check=True)
        print_info("Waiting for Rasa to restart...")
        time.sleep(10)
        return True
    except:
        return False

def test_model():
    """Test the trained model"""
    print_info("Testing Rasa model...")
    
    # Wait for Rasa to be ready
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://localhost:5005/status", timeout=2)
            if response.status_code == 200:
                print_success("Rasa is responding")
                break
        except:
            pass
        
        if attempt < max_attempts - 1:
            print(f"  Waiting for Rasa... ({attempt + 1}/{max_attempts})")
            time.sleep(2)
    else:
        print_warning("Rasa took longer than expected to start")
        return False
    
    # Test queries
    test_queries = [
        "I need help resetting my password",
        "Find me a 3 bedroom house",
        "Order pizza",
        "Schedule an appointment"
    ]
    
    print("\nTesting sample queries:")
    for query in test_queries:
        try:
            response = requests.post(
                "http://localhost:5005/model/parse",
                json={"text": query},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                intent = data['intent']['name']
                confidence = data['intent']['confidence']
                print(f"  ✓ '{query}'")
                print(f"    → Intent: {intent} (confidence: {confidence:.2f})")
            else:
                print_warning(f"  Failed to parse: '{query}'")
        except Exception as e:
            print_warning(f"  Error testing query: {e}")
    
    return True

def main():
    """Main training workflow"""
    print_header("Rasa Model Training for VaaS Platform")
    
    # Step 1: Check Docker
    print("Step 1: Checking prerequisites...")
    if not check_docker():
        print_error("Docker is not running. Please start Docker first.")
        return 1
    print_success("Docker is running")
    
    # Step 2: Check/Start Rasa
    print("\nStep 2: Checking Rasa container...")
    if not check_rasa_container():
        print_warning("Rasa container is not running")
        if not start_rasa():
            print_error("Failed to start Rasa container")
            return 1
    print_success("Rasa container is running")
    
    # Step 3: Merge NLU files
    print("\nStep 3: Merging NLU training data...")
    if not merge_nlu_files():
        print_error("Failed to merge NLU files")
        return 1
    
    # Step 4: Validate configuration
    print("\nStep 4: Validating configuration...")
    if not validate_config():
        print_error("Configuration validation failed")
        return 1
    print_success("All configuration files are present")
    
    # Step 5: Train model
    print("\nStep 5: Training model...")
    if not train_model():
        print_error("Model training failed")
        return 1
    
    # Step 6: Restart Rasa
    print("\nStep 6: Reloading model...")
    if not restart_rasa():
        print_error("Failed to restart Rasa")
        return 1
    print_success("Rasa server restarted")
    
    # Step 7: Test model
    print("\nStep 7: Testing model...")
    test_model()
    
    # Success!
    print_header("✅ Training Complete!")
    print("\nNext steps:")
    print("  1. Load knowledge bases: python scripts/load_all_knowledge.py")
    print("  2. Test via API: curl http://localhost:8000/api/v1/process/text")
    print("  3. Deploy to production: See DEPLOYMENT.md")
    print("\nTest Rasa directly:")
    print("  curl -X POST http://localhost:5005/model/parse \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"text\": \"your test query\"}'")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

