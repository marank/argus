"""Django settings for the Argus backend.

Without any environment variables this is a local development setup (debug on,
SQLite). In the container, docker compose passes the project's root ``.env``;
see ``.env.example`` for all options.
"""

import os
from pathlib import Path
from urllib.parse import urlsplit

from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-only-change-me")
DEBUG = env_bool("DEBUG", True)

# --- Public addresses -----------------------------------------------------------
# APP_URLS lists every URL users open Argus under, e.g.
# "https://argus.example.com,http://argus.intranet:8080". Hosts, CSRF and CORS
# origins and cookie security are all derived from it.
APP_URLS = [urlsplit(url) for url in env_list("APP_URLS")]
_app_origins = [f"{url.scheme}://{url.netloc}" for url in APP_URLS if url.scheme and url.netloc]
# Local dev servers (Vite, runserver) only while debugging.
_dev_origins = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000"] if DEBUG else []

# localhost is always allowed: the container health check calls itself.
ALLOWED_HOSTS = sorted({url.hostname for url in APP_URLS if url.hostname} | {"localhost", "127.0.0.1"})
CSRF_TRUSTED_ORIGINS = _app_origins + _dev_origins
CORS_ALLOWED_ORIGINS = _app_origins + _dev_origins
CORS_ALLOW_CREDENTIALS = True
# Cookies only over HTTPS when Argus is reachable exclusively via HTTPS.
SESSION_COOKIE_SECURE = bool(APP_URLS) and all(url.scheme == "https" for url in APP_URLS)
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "apps.core",
    "apps.accounts",
    "apps.masterdata",
    "apps.inventory",
    "apps.reservations",
    "apps.procurement",
    "apps.dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# PostgreSQL when DB_HOST is set (docker compose), otherwise a local SQLite file.
if os.environ.get("DB_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": os.environ["DB_HOST"],
            "PORT": os.environ.get("DB_PORT", "5432"),
            "NAME": os.environ.get("POSTGRES_DB", "argus"),
            "USER": os.environ.get("POSTGRES_USER", "argus"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
        }
    }
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization: code and data are English, German is shipped as translation.
LANGUAGE_CODE = "en"
LANGUAGES = [("en", _("English")), ("de", _("German"))]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = os.environ.get("TIME_ZONE", "Europe/Berlin")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Behind nginx in the container (and possibly a TLS proxy in front of it).
if env_bool("BEHIND_PROXY", False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True

SESSION_COOKIE_AGE = 60 * 60 * 12  # one working day

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "root": {"handlers": ["console"], "level": os.environ.get("LOG_LEVEL", "INFO")},
    "loggers": {"django.db.backends": {"level": "WARNING"}},
}

if not DEBUG and SECRET_KEY.startswith("django-insecure"):
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured("Set SECRET_KEY when DEBUG is false.")
