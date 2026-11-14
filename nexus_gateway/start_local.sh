#!/bin/bash

# NexusGateway Local Launcher
echo "================================================================"
echo "          Starting NexusGateway LLM Proxy & Dashboard          "
echo "================================================================"

# Ensure Node.js is available (supports standard PATH and NVM)
if ! command -v node &> /dev/null; then
  if [ -d "$HOME/.nvm/versions/node" ]; then
    LATEST_NVM_NODE=$(ls -d "$HOME/.nvm/versions/node"/* 2>/dev/null | tail -n 1)
    if [ -n "$LATEST_NVM_NODE" ]; then
      export PATH="$LATEST_NVM_NODE/bin:$PATH"
    fi
  fi
fi

# Kill existing processes on port 8000 & 3000 if running
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null

# Select Python binary
if [ -f "backend/.venv/bin/python3" ]; then
  PYTHON_BIN="backend/.venv/bin/python3"
elif [ -f "backend/.venv/bin/python" ]; then
  PYTHON_BIN="backend/.venv/bin/python"
elif command -v python3 &> /dev/null; then
  PYTHON_BIN="python3"
else
  PYTHON_BIN="python"
fi

echo "🚀 Starting FastAPI Backend Gateway on http://localhost:8000..."
cd backend
$PYTHON_BIN -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

echo "🎨 Starting React Observability Dashboard on http://localhost:3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ NexusGateway Backend running at: http://localhost:8000"
echo "✅ NexusGateway Swagger Docs at:   http://localhost:8000/docs"
echo "✅ NexusGateway Dashboard at:      http://localhost:3000"
echo "Press Ctrl+C to stop all servers."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
