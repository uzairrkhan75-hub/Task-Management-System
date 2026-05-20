"""Production: PostgreSQL (DATABASE_URL), WhiteNoise compressed static files, HTTPS defaults."""

import os

import dj_database_url

from .base import *  # noqa: F403

# WhiteNoise sits immediately after SecurityMiddleware (production static serving).
_prod_middleware = list(MIDDLEWARE)
MIDDLEWARE = [_prod_middleware[0], "whitenoise.middleware.WhiteNoiseMiddleware", *_prod_middleware[1:]]

_secret = os.environ.get("SECRET_KEY", "").strip()
if not _secret:
    raise ValueError(
        "SECRET_KEY environment variable must be set in production (non-empty)."
    )
SECRET_KEY = _secret

DEBUG = False

ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()]
if not ALLOWED_HOSTS:
    raise ValueError("ALLOWED_HOSTS must list at least one hostname (comma-separated).")

DATABASES = {
    "default": dj_database_url.config(
        env="DATABASE_URL",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

if not DATABASES["default"]:
    raise ValueError("DATABASE_URL must be set in production.")

STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
_use_https = os.environ.get("SECURE_SSL_REDIRECT", "true").lower() in ("1", "true", "yes")
SECURE_SSL_REDIRECT = _use_https
SESSION_COOKIE_SECURE = _use_https
CSRF_COOKIE_SECURE = _use_https

_csrf_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(",") if o.strip()]
if not CSRF_TRUSTED_ORIGINS:
    raise ValueError(
        "CSRF_TRUSTED_ORIGINS must include your site origins (comma-separated), "
        "e.g. https://your-app.onrender.com"
    )
