#!/bin/bash

# DocVector Startup Script
# This script handles the complete startup process for DocVector

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[DocVector]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a service is running on a port
check_port() {
    local port=$1
    if command_exists nc; then
        nc -z localhost "$port" >/dev/null 2>&1
    elif command_exists lsof; then
        lsof -Pi :"$port" -sTCP:LISTEN -t >/dev/null 2>&1
    else
        # Fallback: assume service is running
        return 0
    fi
}

# Print header
echo ""
echo "======================================"
echo "  DocVector Startup Script"
echo "======================================"
echo ""

# Step 1: Check Python version
print_status "Checking Python version..."
if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python $PYTHON_VERSION is installed, but version $REQUIRED_VERSION or higher is required."
    exit 1
fi

print_success "Python $PYTHON_VERSION detected"

# Step 2: Check/Activate virtual environment
print_status "Checking virtual environment..."
if [ ! -d ".venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    python3 -m venv .venv
    print_success "Virtual environment created"
fi

print_status "Activating virtual environment..."
source .venv/bin/activate

print_success "Virtual environment activated"

# Step 3: Check if dependencies are installed
print_status "Checking if dependencies are installed..."
if ! python -c "import fastapi" 2>/dev/null; then
    print_warning "Dependencies not installed. Installing..."
    pip install -e .
    print_success "Dependencies installed"
else
    print_success "Dependencies already installed"
fi

# Step 4: Check .env file
print_status "Checking configuration..."
if [ ! -f ".env" ]; then
    print_warning ".env file not found."
    if [ -f ".env.example" ]; then
        print_status "Copying .env.example to .env..."
        cp .env.example .env
        print_success "Created .env file from .env.example"
    else
        print_error "No .env or .env.example file found. Please create a .env file."
        print_status "You can use the following template:"
        echo ""
        echo "DOCVECTOR_DATABASE_URL=sqlite+aiosqlite:///./docvector.db"
        echo "DOCVECTOR_REDIS_URL=redis://localhost:6379/0"
        echo "DOCVECTOR_QDRANT_HOST=localhost"
        echo "DOCVECTOR_QDRANT_PORT=6333"
        echo ""
        exit 1
    fi
else
    print_success "Configuration file found"
fi

# Step 5: Check external services
print_status "Checking external services..."

# Check Redis
print_status "Checking Redis (port 6379)..."
if check_port 6379; then
    print_success "Redis is running"
else
    print_warning "Redis is not running on port 6379"
    print_status "To start Redis with Docker:"
    echo "  docker run -d --name docvector-redis -p 6379:6379 redis:latest"
    echo ""
    read -p "Continue without Redis? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Qdrant
print_status "Checking Qdrant (port 6333)..."
if check_port 6333; then
    print_success "Qdrant is running"
else
    print_warning "Qdrant is not running on port 6333"
    print_status "To start Qdrant with Docker:"
    echo "  docker run -d --name docvector-qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant:latest"
    echo ""
    print_status "Or use Docker Compose:"
    echo "  docker-compose up -d"
    echo ""
    read -p "Continue without Qdrant? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 6: Initialize database if needed
print_status "Checking database..."
if [ ! -f "docvector.db" ]; then
    print_warning "Database not found. Initializing..."
    python init_db.py
    print_success "Database initialized"
else
    print_success "Database exists"
fi

# Step 7: Start the application
print_status "Starting DocVector API..."
echo ""
echo "======================================"
echo "  DocVector is starting..."
echo "======================================"
echo ""
echo "API will be available at:"
echo "  - Main: http://localhost:8000"
echo "  - Docs: http://localhost:8000/docs"
echo "  - ReDoc: http://localhost:8000/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python -m docvector.api.main
