#!/usr/bin/env bash
set -euo pipefail

if [ -n "${START_COMMAND:-}" ]; then
  echo "Starting with START_COMMAND: ${START_COMMAND}"
  exec /bin/sh -lc "$START_COMMAND"
fi

exec gunicorn --bind 0.0.0.0:${PORT:-8080} server:app
