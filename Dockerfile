FROM node:22-alpine AS web-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM ghcr.io/astral-sh/uv:0.12 AS uv

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/srv/backend/.venv \
    PATH="/srv/backend/.venv/bin:$PATH"
WORKDIR /srv/backend
RUN groupadd --system app && useradd --system --gid app --home-dir /srv app
COPY --from=uv /uv /uvx /bin/
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev
COPY backend/ ./
COPY --from=web-build /build/frontend/dist /srv/frontend/dist
RUN chmod +x start.sh && chown -R app:app /srv
USER app
EXPOSE 8000
CMD ["./start.sh"]
