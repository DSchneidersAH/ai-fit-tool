#!/bin/bash
set -e

APP_NAME="ai-fit-tool"
PORT=8501

echo "🔍 Checking if Docker is running..."
if ! docker info > /dev/null 2>&1; then
  echo "⚠️  Docker is not running."

  # Try to start Docker Desktop depending on OS
  if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🖥️  Launching Docker Desktop for macOS..."
    open -a Docker
  elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🐧 Please manually start Docker daemon (systemctl or dockerd)."
    exit 1
  elif [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "cygwin" ]]; then
    echo "🖥️  Launching Docker Desktop for Windows..."
    powershell.exe -Command "Start-Process 'C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe'"
  else
    echo "❌ Unsupported OS for auto-start. Please start Docker manually."
    exit 1
  fi

  echo "⏳ Waiting for Docker Desktop to start..."
  # Poll until Docker is ready
  while ! docker info > /dev/null 2>&1; do
    sleep 2
  done
  echo "✅ Docker is now running."
fi

# Ensure files exist locally
if [ ! -f "app.py" ]; then
  echo "❌ app.py not found in $(pwd)"
  exit 1
fi
if [ ! -f "style.css" ]; then
  echo "❌ style.css not found in $(pwd)"
  exit 1
fi

echo "🐳 Building Docker image: $APP_NAME"
docker build -t $APP_NAME .

# Stop/remove existing container with same name
if [ "$(docker ps -q -f name=^/${APP_NAME}$)" ]; then
  echo "🛑 Stopping existing container..."
  docker stop $APP_NAME >/dev/null
fi
if [ "$(docker ps -aq -f name=^/${APP_NAME}$)" ]; then
  echo "🧹 Removing old container..."
  docker rm $APP_NAME >/dev/null
fi

# Optional Streamlit config mount (runOnSave + polling)
STREAMLIT_CONFIG_MOUNT=""
if [ -f ".streamlit/config.toml" ]; then
  STREAMLIT_CONFIG_MOUNT="-v $(pwd)/.streamlit/config.toml:/app/.streamlit/config.toml:ro"
fi

echo "🚀 Starting container with hot reload (mounting app.py & style.css)..."
docker run -d \
  --name $APP_NAME \
  -p ${PORT}:8501 \
  -e STREAMLIT_SERVER_RUN_ON_SAVE=true \
  -e STREAMLIT_SERVER_FILE_WATCHER_TYPE=poll \
  -v "$(pwd)/app.py:/app/app.py:rw" \
  -v "$(pwd)/style.css:/app/style.css:rw" \
  $STREAMLIT_CONFIG_MOUNT \
  $APP_NAME

echo "⏳ Waiting a few seconds for Streamlit to start..."
sleep 5

URL="http://localhost:${PORT}"
echo "🌐 Opening browser at $URL"
if command -v open > /dev/null 2>&1; then
  open "$URL"               # macOS
elif command -v xdg-open > /dev/null 2>&1; then
  xdg-open "$URL"           # Linux
elif command -v start > /dev/null 2>&1; then
  start "$URL"              # Windows (Git Bash)
else
  echo "Please open $URL manually in your browser."
fi

echo "✅ Hot reload active. Edits to app.py or style.css will refresh automatically."