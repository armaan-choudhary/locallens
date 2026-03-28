@echo off
setlocal

echo Starting LocalLens Stack...

:: 1. Start Docker services
echo [1/3] Checking Database Services (Milvus/Postgres)...
where docker >nul 2>nul
if errorlevel 1 (
    echo.
    echo Error: Docker is not installed or not in your PATH. 
    echo Please install Docker Desktop for Windows to run LocalLens.
    echo.
    pause
    exit /b 1
)
docker compose up -d

:: 2. Start Backend
echo [2/3] Starting FastAPI Backend...
cd "%~dp0backend"

:: Dependency Check
if exist "%~dp0pradeepika" (
    "%~dp0pradeepika\Scripts\python.exe" check_deps.py
    if errorlevel 1 exit /b 1
) else (
    python check_deps.py
    if errorlevel 1 exit /b 1
)

if exist "%~dp0pradeepika" (
    start /B "" "%~dp0pradeepika\Scripts\python.exe" main.py > backend_server.log 2>&1
) else (
    start /B "" python main.py > backend_server.log 2>&1
)

:: Wait for backend to initialize (server needs a moment to bind)
timeout /t 5 /nobreak > nul

:: 3. Start Frontend
echo [3/3] Starting Vite Frontend...
cd "%~dp0frontend"
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)
start /B "" npm run dev

echo.
echo LocalLens is now running!
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000

:: Open browser
start http://localhost:5173

echo.
echo Close this window to stop (Note: Background processes may still run).
pause
