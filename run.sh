#!/bin/bash

# LocalLens Startup Script (Linux/macOS)
# Runs both the FastAPI backend and Vite frontend

# Colors for logs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting LocalLens Stack...${NC}"

# Wait for a TCP port to become available before starting dependent services.
wait_for_port() {
    local host="$1"
    local port="$2"
    local label="$3"
    local max_attempts=60

    echo -e "${BLUE}Waiting for ${label} on ${host}:${port}...${NC}"
    for ((attempt=1; attempt<=max_attempts; attempt++)); do
        if (echo > "/dev/tcp/${host}/${port}") >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done

    echo -e "${RED:-\033[0;31m}Error: ${label} did not become ready on ${host}:${port}.${NC}"
    return 1
}

wait_for_http() {
    local url="$1"
    local label="$2"
    local max_attempts=60

    echo -e "${BLUE}Waiting for ${label} at ${url}...${NC}"
    for ((attempt=1; attempt<=max_attempts; attempt++)); do
        if curl -fsS "$url" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done

    echo -e "${RED:-\033[0;31m}Error: ${label} did not become ready at ${url}.${NC}"
    return 1
}

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
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed or not in your PATH.${NC}"
    echo -e "Please install Docker to run the LocalLens infrastructure."
    exit 1
fi
docker compose up -d

wait_for_port 127.0.0.1 5432 "Postgres" || exit 1
wait_for_port 127.0.0.1 19530 "Milvus" || exit 1

# 2. Start Backend
echo -e "${GREEN}[2/3] Starting FastAPI Backend...${NC}"
cd backend

# Dependency Check
if [ -d "../.venv" ]; then
    ../.venv/bin/python check_deps.py || exit 1
else
    python3 check_deps.py || exit 1
fi

if [ -d "../.venv" ]; then
    ../.venv/bin/python main.py > backend_server.log 2>&1 &
else
    python3 main.py > backend_server.log 2>&1 &
fi
BACKEND_PID=$!

if ! wait_for_port 127.0.0.1 8000 "FastAPI backend"; then
    echo -e "${RED:-\033[0;31m}Backend failed to start. Check backend/backend_server.log for details.${NC}"
    exit 1
fi

if ! wait_for_http http://127.0.0.1:8000/health "FastAPI backend health"; then
    echo -e "${RED:-\033[0;31m}Backend started listening but did not finish initialization. Check backend/backend_server.log for details.${NC}"
    exit 1
fi

# 3. Start Frontend
echo -e "${GREEN}[3/3] Starting Vite Frontend...${NC}"
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}Installing frontend dependencies...${NC}"
    npm install
fi
npm run dev &
FRONTEND_PID=$!

echo -e "${BLUE}LocalLens is now running!${NC}"
echo -e "Frontend: http://localhost:5173"
echo -e "Backend:  http://localhost:8000"

# Attempt to open browser
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open http://localhost:5173 &> /dev/null &
elif [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:5173 &> /dev/null &
fi

echo -e "Press Ctrl+C to stop all services."

# Keep script alive to catch trap
wait
