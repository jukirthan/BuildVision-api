#!/bin/sh
set -eu

: "${PORT:?PORT must be provided by Railway}"

exec gunicorn run:app \
  --bind "0.0.0.0:${PORT}" \
  --workers 2 \
  --timeout 120
