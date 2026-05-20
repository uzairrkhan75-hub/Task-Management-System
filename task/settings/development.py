"""Local development: SQLite, DEBUG on. Default when using task.settings."""

import os

from .base import *  # noqa: F403

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-39np(amtl$j5x!&na&75lvys*cik)3da6j_z%46f#-g609@47i",
)

DEBUG = True

_hosts = os.environ.get("ALLOWED_HOSTS", "")
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
ALLOWED_HOSTS.extend(h.strip() for h in _hosts.split(",") if h.strip())

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}
