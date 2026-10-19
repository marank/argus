# syntax=docker/dockerfile:1.7
#
# Argus: one image with nginx (static frontend + reverse proxy), gunicorn (Django)
# and supervisord keeping both alive. Runs as an unprivileged user on port 8080.

ARG PYTHON_VERSION=3.14
ARG NODE_VERSION=24

# --- 1. Frontend build ---------------------------------------------------------
FROM node:${NODE_VERSION}-alpine AS frontend
WORKDIR /build
RUN corepack enable
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile
COPY frontend/ ./
# Type-check and build; a type error fails the image build.
RUN pnpm build

# --- 2. Python dependencies ------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-trixie AS backend
COPY --from=ghcr.io/astral-sh/uv:0.12.18 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# --- 3. Runtime ------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-trixie AS runtime

LABEL org.opencontainers.image.title="Argus" \
      org.opencontainers.image.description="IT asset management (Django + Vue)"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings \
    DEBUG=false \
    BEHIND_PROXY=true

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx supervisor curl \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default \
    && groupadd --system --gid 10001 argus \
    && useradd --system --uid 10001 --gid argus --home-dir /app --shell /usr/sbin/nologin argus

WORKDIR /app
COPY --from=backend /app/.venv /app/.venv
COPY --chown=argus:argus backend/ /app/
COPY --from=frontend /build/dist /app/frontend
COPY --chown=argus:argus docker/ /app/docker/

# Static files for the Django admin and API docs; a throwaway key is enough here.
RUN SECRET_KEY=collectstatic-only python manage.py collectstatic --noinput --verbosity 0 \
    && chmod +x /app/docker/entrypoint.sh \
    && chown -R argus:argus /app/staticfiles

USER argus
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8080/api/health || exit 1

# The entrypoint execs supervisord, which then runs as PID 1: it forwards
# `docker stop` to nginx/gunicorn and reaps finished child processes.
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["supervisord", "-c", "/app/docker/supervisord.conf"]
