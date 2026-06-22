#!/usr/bin/env bash
echo "Starting Song Manager..."
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""

uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

cd frontend && npm run dev &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
