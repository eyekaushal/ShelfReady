"""
Django settings for ShelfReady.

Every secret or environment-specific value comes from environment variables
(or a local `.env` file in development). See `.env.example` for the full list.
"""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# Read backend/.env if it exists (local dev). On Render, real env vars are used instead.
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

# --- Core -------------------------------------------------------------------

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",  # trigram search lookups (pg_trgm)
    # third-party
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",  # stores logged-out refresh tokens
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    # our apps
    "common",
    "accounts",
    "catalog",
    "ai",
    "imports",
]

MIDDLEWARE = [
    # Request id first, so every log line after it (including errors) has the id.
    "common.request_id_middleware.RequestIdMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serves admin static files on Render
    "corsheaders.middleware.CorsMiddleware",  # must be before CommonMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

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

# --- Database ---------------------------------------------------------------

# One DATABASE_URL works for local Docker and for Neon (Neon adds ?sslmode=require).
DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["CONN_MAX_AGE"] = 60  # reuse connections for a minute
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True  # drop dead ones (Neon sleeps)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Auth -------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- i18n / time ------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# --- Static files -----------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# --- CORS / CSRF (React on Vercel talks to this API) -------------------------

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:5173"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# --- Production security ----------------------------------------------------

if not DEBUG:
    # Render terminates HTTPS at its proxy and forwards this header.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# --- Django REST Framework --------------------------------------------------

REST_FRAMEWORK = {
    # The React app sends "Authorization: Bearer <access token>" on every request.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    # Anyone can read; writing needs login. Owner checks are added per view.
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticatedOrReadOnly"],
    # One error shape for every API error (see common/exception_handler.py).
    "EXCEPTION_HANDLER": "common.exception_handler.handle_exception",
    # Every list endpoint is paginated: {"count", "next", "previous", "results"}.
    "DEFAULT_PAGINATION_CLASS": "common.pagination.standard_pagination.StandardPagination",
    # drf-spectacular reads our views + serializers and builds the OpenAPI schema.
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Views opt in with `throttle_scope = "..."`. Limits are per user (or per IP if anonymous).
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {
        "auth": env("THROTTLE_AUTH", default="20/min"),  # slows down password guessing
        "ai": env("THROTTLE_AI", default="20/hour"),  # AI calls cost money: per user, per hour
    },
}

# --- API docs (drf-spectacular) ------------------------------------------------

SPECTACULAR_SETTINGS = {
    "TITLE": "ShelfReady API",
    "DESCRIPTION": (
        "A recognition-ready product catalog (SKU master) for retail shelf recognition.\n\n"
        "**Auth:** call `POST /api/auth/login/`, then click *Authorize* and paste the `access` token.\n\n"
        "**Errors** always look like "
        '`{"error": {"code": "...", "message": "...", "details": {...}}}`.'
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,  # don't list the schema endpoint inside itself
    # Separate "request" and "response" models, so read-only fields (id, created_by...)
    # don't show up as inputs in Swagger.
    "COMPONENT_SPLIT_REQUEST": True,
}

# --- JWT (djangorestframework-simplejwt) --------------------------------------

SIMPLE_JWT = {
    # Short-lived access token; the frontend silently refreshes it with the refresh token.
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    # Each refresh returns a NEW refresh token and blacklists the old one,
    # so a stolen refresh token stops working after it's used once.
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}

# --- AI (Anthropic Claude) ------------------------------------------------------

# Empty key = AI features switch off cleanly ("AI unavailable"); the rest of the app still works.
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", default="")
ANTHROPIC_MODEL_VISION = env("ANTHROPIC_MODEL_VISION", default="claude-sonnet-5-5")  # reads pack photos
ANTHROPIC_MODEL_FAST = env("ANTHROPIC_MODEL_FAST", default="claude-haiku-5-5")  # short text tasks
AI_TIMEOUT_SECONDS = env.float("AI_TIMEOUT_SECONDS", default=40.0)

# Images we fetch or receive (photo → form, and later pHash / blur checks).
IMAGE_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
IMAGE_FETCH_TIMEOUT_SECONDS = env.float("IMAGE_FETCH_TIMEOUT_SECONDS", default=5.0)

# Same-origin uploads are capped a bit above the image limit, so Django rejects huge bodies early.
DATA_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024

# Identical AI searches are cached briefly (Block 8); local memory is enough for one instance.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# --- Seed data ------------------------------------------------------------------

# Password for the public demo account created by `manage.py seed_catalog` (shown in the README).
SEED_DEMO_PASSWORD = env("SEED_DEMO_PASSWORD", default="ShelfReady@2026")

# --- Celery -----------------------------------------------------------------

# Locally (Docker) a worker picks tasks from Redis. On Render there is no worker,
# so ALWAYS_EAGER=True runs the same task code inline inside the request.
CELERY_BROKER_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=True)
CELERY_TASK_EAGER_PROPAGATES = True  # in eager mode, task errors surface instead of hiding

# --- Logging (structured JSON, one line per event) ---------------------------

LOG_LEVEL = env("LOG_LEVEL", default="INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_id": {"()": "common.log.request_id_filter.RequestIdFilter"},
    },
    "formatters": {
        "json": {"()": "common.log.json_formatter.JsonFormatter"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["request_id"],
        },
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        # Our middleware already logs every request, so silence Django's duplicate line.
        "django.request": {"level": "ERROR"},
        "django.server": {"level": "WARNING"},
        # The HTTP library logs every request at INFO; our own "ai call" lines are enough.
        "httpx2": {"level": "WARNING"},
    },
}
