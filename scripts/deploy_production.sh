#!/bin/bash

# Voice-as-a-Service Production Deployment Script
# One-command deployment for production environments

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${BOLD}${'='*70}${NC}"
    echo -e "${BOLD}$1${NC}"
    echo -e "${BOLD}${'='*70}${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Main deployment
print_header "Voice-as-a-Service Platform - Production Deployment"

# Step 1: Pre-flight checks
print_info "Step 1: Running pre-flight checks..."
echo "--------------------------------------"

# Check Docker
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running"
    exit 1
fi
print_success "Docker is running"

# Check Docker Compose
if ! docker-compose version > /dev/null 2>&1; then
    print_error "Docker Compose is not installed"
    exit 1
fi
print_success "Docker Compose is installed"

# Check .env file
if [ ! -f ".env" ]; then
    print_error ".env file not found"
    print_info "Run: cp .env.example .env and configure it"
    exit 1
fi
print_success ".env file exists"

# Check if OpenAI API key is configured
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    print_warning "OpenAI API key may not be configured in .env"
    print_info "Make sure to add your OpenAI API key"
fi

echo ""

# Step 2: Create directories
print_info "Step 2: Creating necessary directories..."
echo "--------------------------------------"

mkdir -p logs tmp models data backups
print_success "Directories created"

echo ""

# Step 3: Build Docker images
print_info "Step 3: Building Docker images..."
echo "--------------------------------------"

docker-compose build --no-cache
print_success "Docker images built"

echo ""

# Step 4: Start infrastructure services
print_info "Step 4: Starting infrastructure services..."
echo "--------------------------------------"

docker-compose up -d postgres redis qdrant
print_success "Infrastructure services started"

print_info "Waiting for services to be ready..."
sleep 15

echo ""

# Step 5: Initialize databases
print_info "Step 5: Initializing databases..."
echo "--------------------------------------"

if docker-compose exec -T vaas_app python scripts/init_db.py; then
    print_success "Database initialized"
    print_warning "IMPORTANT: Save the API key displayed above!"
else
    print_warning "Database may already be initialized"
fi

echo ""

# Step 6: Train Rasa model
print_info "Step 6: Training Rasa model..."
echo "--------------------------------------"

if [ -f "scripts/train_rasa.py" ]; then
    python3 scripts/train_rasa.py
    print_success "Rasa model trained"
else
    print_warning "Training script not found, skipping"
fi

echo ""

# Step 7: Load knowledge bases
print_info "Step 7: Loading knowledge bases..."
echo "--------------------------------------"

if [ -f "scripts/load_all_knowledge.py" ]; then
    python3 scripts/load_all_knowledge.py
    print_success "Knowledge bases loaded"
else
    print_warning "Knowledge loading script not found, skipping"
fi

echo ""

# Step 8: Start application services
print_info "Step 8: Starting application services..."
echo "--------------------------------------"

docker-compose up -d vaas_app rasa
print_success "Application services started"

print_info "Waiting for services to be ready..."
sleep 20

echo ""

# Step 9: Start monitoring
print_info "Step 9: Starting monitoring services..."
echo "--------------------------------------"

docker-compose up -d prometheus grafana
print_success "Monitoring services started"

echo ""

# Step 10: Health checks
print_info "Step 10: Running health checks..."
echo "--------------------------------------"

max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Platform is responding"
        
        # Get detailed health status
        health_response=$(curl -s http://localhost:8000/health)
        echo "$health_response" | python3 -m json.tool 2>/dev/null || echo "$health_response"
        break
    fi
    
    attempt=$((attempt + 1))
    echo "Waiting for platform... ($attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    print_warning "Platform took longer than expected to start"
    print_info "Check logs: docker-compose logs -f vaas_app"
fi

echo ""

# Summary
print_header "✅ Deployment Complete!"

echo -e "${BOLD}Service Status:${NC}"
docker-compose ps

echo ""
echo -e "${BOLD}Access Points:${NC}"
echo "  • API Gateway:    http://localhost:8000"
echo "  • API Docs:       http://localhost:8000/docs"
echo "  • Prometheus:     http://localhost:9091"
echo "  • Grafana:        http://localhost:3000 (admin/admin)"

echo ""
echo -e "${BOLD}Next Steps:${NC}"
echo "  1. Save your API key from Step 5"
echo "  2. Test the API:"
echo "     curl -X POST http://localhost:8000/api/v1/process/text \\"
echo "       -H 'Authorization: Bearer YOUR_API_KEY' \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"text\":\"test\",\"user_id\":\"user1\",\"domain\":\"customer_support\"}'"
echo "  3. Setup SSL/HTTPS for production"
echo "  4. Configure domain name"
echo "  5. Setup automated backups"

echo ""
echo -e "${BOLD}Useful Commands:${NC}"
echo "  • View logs:       docker-compose logs -f"
echo "  • Stop platform:   docker-compose down"
echo "  • Restart:         docker-compose restart"
echo "  • Health check:    curl http://localhost:8000/health"

echo ""
echo -e "${GREEN}Platform deployed successfully! 🚀${NC}"
echo ""

