#!/bin/bash

# LocalLens Startup Script
# Runs both the FastAPI backend and Vite frontend

# Colors for logs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting LocalLens Stack...${NC}"

# Function to handle shutdown
cleanup() {
    echo -e "\n${BLUE}Shutting down LocalLens...${NC}"
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit
}

# Trap ctrl+c
trap cleanup SIGINT

# 1. Start Docker services (if not already running)
echo -e "${GREEN}[1/3] Checking Database Services (Milvus/Postgres)...${NC}"
docker compose up -d

# 2. Start Backend
echo -e "${GREEN}[2/3] Starting FastAPI Backend...${NC}"
if [ -d "./.venv" ]; then
    ./.venv/bin/python main.py &
else
    python3 main.py &
fi
BACKEND_PID=$!

# Wait a few seconds for backend to initialize models
sleep 5

# 3. Start Frontend
echo -e "${GREEN}[3/3] Starting Vite Frontend...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!

echo -e "${BLUE}LocalLens is now running!${NC}"
echo -e "Frontend: http://localhost:5173"
echo -e "Backend:  http://localhost:8000"
echo -e "Press Ctrl+C to stop all services."

# Keep script alive to catch trap
wait
