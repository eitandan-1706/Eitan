@echo off
echo Starting Song Manager...
start "Backend" cmd /k "python -m uvicorn backend.main:app --reload"
timeout /t 2 /nobreak >nul
start "Frontend" cmd /k "cd frontend && npm run dev"
echo Both servers started. Open http://localhost:5173
