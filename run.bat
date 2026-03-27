@echo off
setlocal

echo Starting LocalLens Stack...

:: 1. Start Docker services
echo [1/3] Checking Database Services (Milvus/Postgres)...
docker compose up -d

:: 2. Start Backend
echo [2/3] Starting FastAPI Backend...
cd backend
if exist "../.venv" (
    start /B ../.venv/Scripts/python.exe main.py
) else (
    start /B python main.py
)

:: Wait for backend to initialize
timeout /t 5 /nobreak > nul

:: 3. Start Frontend
echo [3/3] Starting Vite Frontend...
cd ../frontend
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)
start /B npm run dev

echo.
echo LocalLens is now running!
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000
echo Close this window to stop (Note: Background processes may still run).
pause
