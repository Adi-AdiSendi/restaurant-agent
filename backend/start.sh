#!/bin/sh
set -eu
# The container is only reachable through Railway's proxy, so trust its forwarded headers.
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" \
    --proxy-headers --forwarded-allow-ips="*"
