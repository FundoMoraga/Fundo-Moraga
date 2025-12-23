#!/usr/bin/env bash
set -euo pipefail

if [ -n "${START_COMMAND:-}" ]; then
  echo "Starting with START_COMMAND: ${START_COMMAND}"
  exec /bin/sh -lc "$START_COMMAND"
fi

# Gunicorn con logs a stdout/stderr para que Railway los muestre
exec gunicorn \
  --bind 0.0.0.0:${PORT:-8080} \
  --access-logfile - \
  --error-logfile - \
  --capture-output \
  --log-level info \
  server:app
