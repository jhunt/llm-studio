#!/bin/sh
set -eu

env | grep LLM_
if ! test -f $LLM_STUDIO_DB; then
  echo ">> initializing '$LLM_STUDIO_DB' from /app/schema.sql..."
  mkdir -p "$(dirname "$LLM_STUDIO_DB")"
  sqlite3 </app/schema.sql "$LLM_STUDIO_DB"
fi
exec gunicorn app:app \
  --bind 0.0.0.0:${PORT:-5000} \
  --workers ${GUNICORN_WORKERS:-3} \
  --timeout ${GUNICORN_TIMEOUT:-300}
