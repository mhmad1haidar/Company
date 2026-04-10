"""Local development settings."""

from .base import *  # noqa: F403

DEBUG = True

# HTTP localhost: cookies must not be marked Secure or browsers will not send them.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Optional: relax CORS in dev if frontend runs on another port
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=True)  # noqa: F405
