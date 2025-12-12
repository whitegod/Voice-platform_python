#!/bin/bash

# Rasa Training Script for VaaS Platform
# Trains Rasa model with all domain intents

set -e

echo "========================================"
echo "Rasa Model Training Script"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if Rasa container exists
if ! docker-compose ps rasa | grep -q "Up"; then
    echo -e "${YELLOW}⚠️  Rasa container is not running. Starting it...${NC}"
    docker-compose up -d rasa
    echo "Waiting for Rasa to start..."
    sleep 10
fi

echo -e "${GREEN}✓ Docker and Rasa are running${NC}"
echo ""

# Merge all NLU training files
echo "Step 1: Merging NLU training data..."
echo "--------------------------------------"

# Check if domain-specific NLU files exist
if [ -f "config/rasa/customer_support_nlu.yml" ]; then
    echo "  - Merging customer_support_nlu.yml"
    cat config/rasa/customer_support_nlu.yml >> config/rasa/nlu.yml
fi

# Note: Add other domain NLU files as you create them
# Example:
# if [ -f "config/rasa/healthcare_nlu.yml" ]; then
#     cat config/rasa/healthcare_nlu.yml >> config/rasa/nlu.yml
# fi

echo -e "${GREEN}✓ NLU data merged${NC}"
echo ""

# Update domain.yml with all entities and intents
echo "Step 2: Validating Rasa configuration..."
echo "--------------------------------------"

# Check if required files exist
if [ ! -f "config/rasa/nlu.yml" ]; then
    echo -e "${RED}❌ config/rasa/nlu.yml not found${NC}"
    exit 1
fi

if [ ! -f "config/rasa/domain.yml" ]; then
    echo -e "${RED}❌ config/rasa/domain.yml not found${NC}"
    exit 1
fi

if [ ! -f "config/rasa/config.yml" ]; then
    echo -e "${RED}❌ config/rasa/config.yml not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All configuration files present${NC}"
echo ""

# Train the model
echo "Step 3: Training Rasa model..."
echo "--------------------------------------"
echo "This may take several minutes..."
echo ""

# Train inside the Rasa container
docker-compose exec -T rasa rasa train \
    --config /app/config.yml \
    --domain /app/domain.yml \
    --data /app/nlu.yml \
    --out /app/models

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Model trained successfully!${NC}"
else
    echo ""
    echo -e "${RED}❌ Training failed. Check the logs above.${NC}"
    exit 1
fi

echo ""

# Restart Rasa to load the new model
echo "Step 4: Restarting Rasa server..."
echo "--------------------------------------"

docker-compose restart rasa

echo "Waiting for Rasa to reload..."
sleep 10

echo -e "${GREEN}✓ Rasa server restarted${NC}"
echo ""

# Test the model
echo "Step 5: Testing Rasa model..."
echo "--------------------------------------"

# Wait for Rasa to be ready
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:5005/status > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Rasa is responding${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo "Waiting for Rasa... ($attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${YELLOW}⚠️  Rasa took longer than expected to start${NC}"
fi

# Test with a sample query
echo ""
echo "Testing with sample queries:"

# Test customer support intent
echo "  - Testing: 'I need help resetting my password'"
response=$(curl -s -X POST http://localhost:5005/model/parse \
    -H "Content-Type: application/json" \
    -d '{"text": "I need help resetting my password"}')

intent=$(echo $response | python3 -c "import sys, json; print(json.load(sys.stdin)['intent']['name'])" 2>/dev/null || echo "unknown")
confidence=$(echo $response | python3 -c "import sys, json; print(json.load(sys.stdin)['intent']['confidence'])" 2>/dev/null || echo "0.0")

echo "    Intent: $intent (confidence: $confidence)"

echo ""
echo "========================================"
echo -e "${GREEN}✅ Rasa Training Complete!${NC}"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Test more queries via API"
echo "  2. Load knowledge base data: ./scripts/load_all_knowledge.sh"
echo "  3. Start the platform: docker-compose up -d"
echo ""
echo "Test Rasa directly:"
echo "  curl -X POST http://localhost:5005/model/parse \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"text\": \"your test query\"}'"
echo ""

