#!/bin/sh
set -e
if [ -n "${START_COMMAND:-}" ]; then
  echo "Starting with START_COMMAND: ${START_COMMAND}"
  exec sh -c "$START_COMMAND"
fi

# Inyectar configuraciones dinámicas en HTMLs (GA ID, etc)
echo "🔧 Inyectando configuraciones en archivos HTML..."
python3 build_inject_config.py || echo "⚠️  Build script falló, continuando..."

# Gunicorn con logs a stdout/stderr para que Railway los muestre
PORT_VALUE="${PORT:-8080}"
exec gunicorn \
  --bind "0.0.0.0:${PORT_VALUE}" \
  --workers "${WORKERS:-4}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --access-logfile - \
  --error-logfile - \
  --capture-output \
  --log-level info \
  server:app
