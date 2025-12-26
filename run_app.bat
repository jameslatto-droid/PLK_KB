@echo off
setlocal

REM Simple launcher for PLK_KB (Windows cmd). Starts backend via Docker Compose, then the UI.

set "ROOT=%~dp0"
set "COMPOSE_FILE=%ROOT%ops\docker\docker-compose.yml"

echo [RUN] Starting backend services...
docker compose -f "%COMPOSE_FILE%" up -d
if errorlevel 1 (
  echo [RUN] Failed to start backend services. Ensure Docker Compose v2 is installed.
  exit /b 1
)

echo [RUN] Installing UI dependencies (if needed)...
pushd "%ROOT%apps\ui"
if not exist node_modules (
  npm install
  if errorlevel 1 (
    echo [RUN] npm install failed.
    popd
    exit /b 1
  )
)

echo [RUN] Starting UI (Ctrl+C to stop)...
npm run dev
popd

echo [RUN] Done.
endlocal
