#!/bin/sh
if [ -n "${START_COMMAND:-}" ]; then
  echo "Starting with START_COMMAND: ${START_COMMAND}"
  exec sh -c "$START_COMMAND"
fi

# Inyectar configuraciones dinamicas en HTMLs (GA ID, etc)
echo "[BUILD] Inyectando configuraciones en archivos HTML..."
python3 build_inject_config.py || echo "[BUILD] Build script fallo, continuando..."
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --access-logfile - \
  --error-logfile - \
  --capture-output \
  --log-level info \
  server:app
