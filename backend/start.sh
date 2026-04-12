#!/bin/bash
# CodeGuard Backend Startup Script

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== CodeGuard Backend Startup ===${NC}"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found, copying from .env.example${NC}"
    cp .env.example .env
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}Python version: ${PYTHON_VERSION}${NC}"

# Install dependencies if needed
if [ ! -d "node_modules" ] && [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip install -r requirements.txt
fi

# Create uploads directory
mkdir -p uploads

# Start server
echo -e "${GREEN}Starting FastAPI server...${NC}"
echo -e "${GREEN}API Docs: http://localhost:8000/api/docs${NC}"
echo -e "${GREEN}Health Check: http://localhost:8000/health${NC}"

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload