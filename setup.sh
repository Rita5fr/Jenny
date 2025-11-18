#!/bin/bash
# Jenny Assistant - Automated Setup Script
# This script automates the installation and setup of Jenny

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "============================================"
echo "  Jenny AI Assistant - Automated Setup"
echo "============================================"
echo ""

# Function to print status messages
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if running in Jenny directory
if [ ! -f "requirements.txt" ]; then
    print_error "Please run this script from the Jenny directory"
    exit 1
fi

print_status "Found Jenny directory"

# Step 1: Check Python version
echo ""
echo "Step 1: Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    print_status "Python $PYTHON_VERSION detected (>= 3.11 required)"
else
    print_error "Python 3.11 or higher required. Found: $PYTHON_VERSION"
    echo "Install Python 3.11+: https://www.python.org/downloads/"
    exit 1
fi

# Step 2: Check Docker
echo ""
echo "Step 2: Checking Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    print_status "Docker $DOCKER_VERSION detected"

    # Check if Docker is running
    if docker info &> /dev/null; then
        print_status "Docker daemon is running"
    else
        print_error "Docker is installed but not running"
        echo "Please start Docker Desktop or Docker daemon"
        exit 1
    fi
else
    print_error "Docker not found"
    echo "Install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose
if docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version | awk '{print $4}')
    print_status "Docker Compose $COMPOSE_VERSION detected"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | awk '{print $4}')
    print_status "Docker Compose $COMPOSE_VERSION detected"
    COMPOSE_CMD="docker-compose"
else
    print_error "Docker Compose not found"
    echo "Docker Compose comes with Docker Desktop"
    exit 1
fi

# Use docker compose if available, otherwise docker-compose
COMPOSE_CMD=${COMPOSE_CMD:-"docker compose"}

# Step 3: Install Python dependencies
echo ""
echo "Step 3: Installing Python dependencies..."
if pip3 install -r requirements.txt --quiet; then
    print_status "Python dependencies installed"
else
    print_error "Failed to install Python dependencies"
    exit 1
fi

# Step 4: Configure environment
echo ""
echo "Step 4: Configuring environment..."

if [ -f ".env" ]; then
    print_warning ".env file already exists"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Keeping existing .env file"
    else
        cp .env.example .env
        print_status "Created new .env file from template"
    fi
else
    cp .env.example .env
    print_status "Created .env file from template"
fi

# Check if OpenAI API key is set
if grep -q "OPENAI_API_KEY=your-openai-api-key-here" .env || grep -q "OPENAI_API_KEY=$" .env; then
    print_warning "OpenAI API key not configured"
    echo ""
    echo "You need to add your OpenAI API key to .env file"
    echo "Get your API key from: https://platform.openai.com/api-keys"
    echo ""
    read -p "Enter your OpenAI API key (or press Enter to skip): " API_KEY

    if [ ! -z "$API_KEY" ]; then
        # Replace the placeholder with actual key
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$API_KEY/" .env
        else
            # Linux
            sed -i "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$API_KEY/" .env
        fi
        print_status "OpenAI API key configured"
    else
        print_warning "You'll need to manually add your API key to .env before running Jenny"
    fi
else
    print_status "OpenAI API key already configured"
fi

# Step 5: Start Docker services
echo ""
echo "Step 5: Starting Docker services (PostgreSQL, Redis, Neo4j)..."
echo "This may take 30-60 seconds for first-time setup..."

if $COMPOSE_CMD up -d; then
    print_status "Docker services started"
else
    print_error "Failed to start Docker services"
    exit 1
fi

# Wait for services to be healthy
echo ""
echo "Waiting for services to be ready..."
sleep 5

# Check PostgreSQL
echo -n "  Checking PostgreSQL... "
for i in {1..30}; do
    if docker exec jenny-postgres pg_isready -U jenny &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ (timeout)${NC}"
        print_warning "PostgreSQL might not be ready yet"
    fi
    sleep 1
done

# Check Redis
echo -n "  Checking Redis... "
for i in {1..30}; do
    if docker exec jenny-redis redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ (timeout)${NC}"
        print_warning "Redis might not be ready yet"
    fi
    sleep 1
done

# Check Neo4j
echo -n "  Checking Neo4j... "
for i in {1..60}; do
    if docker exec jenny-neo4j wget -q --spider http://localhost:7474 &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
        break
    fi
    if [ $i -eq 60 ]; then
        echo -e "${RED}✗ (timeout)${NC}"
        print_warning "Neo4j might still be initializing (it can take up to 2 minutes)"
    fi
    sleep 1
done

# Step 6: Display final instructions
echo ""
echo "============================================"
echo -e "${GREEN}✓ Installation Complete!${NC}"
echo "============================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Start Mem0 service (Terminal 1):"
echo "   python -m uvicorn app.mem0.server.main:app --port 8081"
echo ""
echo "2. Start Jenny main app (Terminal 2):"
echo "   python -m uvicorn app.main:app --port 8044"
echo ""
echo "3. Test the installation:"
echo "   curl http://localhost:8044/health"
echo ""
echo "Database access:"
echo "  - PostgreSQL: localhost:5432 (user: jenny, password: jenny123)"
echo "  - Redis:      localhost:6379"
echo "  - Neo4j:      http://localhost:7474 (user: neo4j, password: jenny123)"
echo ""
echo "Documentation:"
echo "  - Quick Start: README.md"
echo "  - Full Guide:  SETUP.md"
echo ""
echo "Useful commands:"
echo "  - Stop services:   $COMPOSE_CMD down"
echo "  - View logs:       $COMPOSE_CMD logs -f"
echo "  - Restart service: $COMPOSE_CMD restart postgres"
echo ""

# Optional: Ask if user wants to start services now
echo ""
read -p "Do you want to start Jenny services now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Starting services..."
    echo "Press Ctrl+C to stop"
    echo ""

    # Start Mem0 in background
    python -m uvicorn app.mem0.server.main:app --port 8081 &
    MEM0_PID=$!
    sleep 3

    # Start main app
    python -m uvicorn app.main:app --port 8044 &
    MAIN_PID=$!

    sleep 3

    # Test health endpoint
    echo ""
    echo "Testing health endpoint..."
    if curl -s http://localhost:8044/health | grep -q "ok"; then
        print_status "Jenny is running! Access at http://localhost:8044"
    else
        print_warning "Services started but health check failed"
    fi

    echo ""
    echo "Services running in background"
    echo "  Mem0 PID:  $MEM0_PID"
    echo "  Main PID:  $MAIN_PID"
    echo ""
    echo "To stop services:"
    echo "  kill $MEM0_PID $MAIN_PID"
    echo "  $COMPOSE_CMD down"

    # Keep script running
    wait
fi
