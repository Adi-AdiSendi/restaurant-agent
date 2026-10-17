#!/bin/sh
set -eu
# Render runs this from backend/ after the build. The app is only reached
# through Render's proxy (and Netlify's in front of it), so trust forwarded headers.
exec uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" \
    --proxy-headers --forwarded-allow-ips="*"
