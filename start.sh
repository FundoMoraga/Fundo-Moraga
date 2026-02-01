#!/bin/sh

if [ -n "${START_COMMAND:-}" ]; then
  echo "Starting with START_COMMAND: ${START_COMMAND}"
  exec sh -c "$START_COMMAND"
fi

# Inyectar configuraciones dinamicas en HTMLs (GA ID, etc)
echo "[BUILD] Inyectando configuraciones en archivos HTML..."
python3 build_inject_config.py || echo "[BUILD] Build script fallo, continuando..."

# Gunicorn con logs a stdout/stderr
PORT_VALUE="${PORT:-8080}"
WORKERS="${WORKERS:-4}"
TIMEOUT="${GUNICORN_TIMEOUT:-60}"

exec gunicorn \
  --bind "0.0.0.0:${PORT_VALUE}" \
  --workers "${WORKERS}" \
  --timeout "${TIMEOUT}" \
  --error-logfile - \
  --capture-output \
  --log-level info \
  server:app
