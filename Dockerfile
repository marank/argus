# syntax=docker/dockerfile:1.28@sha256:bb22d9815c728170f72750f4e5b0d672e06176142e1d602c7e66c050100b7e5b
#
# Argus: one image with nginx (static frontend and documentation + reverse proxy), gunicorn (Django)
# and supervisord keeping both alive. Runs as an unprivileged user on port 8080.
#
# Images are pinned by tag and the digest of their multi-platform index; Dependabot updates both.

# --- 1. Frontend build ---------------------------------------------------------
FROM node:26-alpine@sha256:6bd9ab43c0ec0190ca7b2d193906cb8b7edf6e7f4afa43ddeccd6452710bffb5 AS frontend
WORKDIR /build
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
# pnpm in the version of packageManager; through npm, as Node 25+ no longer ships corepack.
RUN npm install -g "$(node -p "require('./package.json').packageManager")"
RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile
COPY frontend/ ./
# Type-check and build; a type error fails the image build.
RUN pnpm build

# --- 2. Documentation ------------------------------------------------------------
FROM node:26-alpine@sha256:6bd9ab43c0ec0190ca7b2d193906cb8b7edf6e7f4afa43ddeccd6452710bffb5 AS docs
WORKDIR /build
COPY docs/package.json docs/pnpm-lock.yaml docs/pnpm-workspace.yaml ./
# pnpm in the version of packageManager; through npm, as Node 25+ no longer ships corepack.
RUN npm install -g "$(node -p "require('./package.json').packageManager")"
RUN --mount=type=cache,target=/root/.local/share/pnpm/store     pnpm install --frozen-lockfile
COPY docs/ ./
RUN pnpm build

# --- 3. Python dependencies ------------------------------------------------------
FROM python:3.14-slim-trixie@sha256:9aaa474097d094040649f2162a627c0049b408f52138d980916788d80f04802f AS backend
COPY --from=ghcr.io/astral-sh/uv:0.13.4@sha256:9f130421e930bfbdc563c00740466603f8723158e90297d07957c2294640262b /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# --- 4. Runtime ------------------------------------------------------------------
FROM python:3.14-slim-trixie@sha256:9aaa474097d094040649f2162a627c0049b408f52138d980916788d80f04802f AS runtime
ARG SUPERVISOR_VERSION=4.3.0
# pg_dump for the nightly backups; its major version must be at least the server's
# (postgres image in compose.yml). Debian's own client lags behind, so it comes from
# the PostgreSQL project's repository.
ARG POSTGRES_MAJOR=18

LABEL org.opencontainers.image.title="Argus" \
      org.opencontainers.image.description="IT asset management (Django + Vue)"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings \
    DEBUG=false \
    BEHIND_PROXY=true \
    BACKUP_DIR=/backups

# Upgraded too: the base image gets Debian's security fixes only with its next release.
# Builds skip the cache for this stage (--no-cache-filter runtime), so the packages
# are current with every build.
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends nginx curl ca-certificates \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc -o /usr/share/keyrings/pgdg.asc \
    && echo "deb [signed-by=/usr/share/keyrings/pgdg.asc] https://apt.postgresql.org/pub/repos/apt trixie-pgdg main" \
        > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends "postgresql-client-${POSTGRES_MAJOR}" \
    && rm -rf /var/lib/apt/lists/* \
    # supervisord from PyPI, outside the app's venv: it is infrastructure, not an app
    # dependency (Debian's package would also bring setuptools). pip is not needed at
    # runtime, so it goes afterwards, with the libraries it vendors.
    && pip install --no-cache-dir --root-user-action=ignore "supervisor==${SUPERVISOR_VERSION}" \
    && pip uninstall -y --root-user-action=ignore pip \
    && rm -f /etc/nginx/sites-enabled/default \
    && groupadd --system --gid 10001 argus \
    && useradd --system --uid 10001 --gid argus --home-dir /app --shell /usr/sbin/nologin argus \
    # Mount point of the backups volume: a new volume takes over owner and mode, so the
    # app user can write dumps there while the root filesystem stays read-only.
    && install -d -o argus -g argus -m 0700 /backups

WORKDIR /app
COPY --from=backend /app/.venv /app/.venv
# Code and configuration stay owned by root: the app user can read but not change them.
COPY backend/ /app/
COPY --from=frontend /build/dist /app/frontend
COPY --from=docs /build/.vitepress/dist /app/docs
COPY docker/ /app/docker/

# Static files for the Django admin; a throwaway (random) key is enough here.
RUN SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')" \
    python manage.py collectstatic --noinput --verbosity 0 \
    && chmod +x /app/docker/entrypoint.sh

USER argus
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8080/api/health || exit 1

# The entrypoint execs supervisord, which then runs as PID 1: it forwards
# `docker stop` to nginx/gunicorn and reaps finished child processes.
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["supervisord", "-c", "/app/docker/supervisord.conf"]
