"""Production-oriented settings. Set DEBUG=False and strong SECRET_KEY via environment."""

from .base import *  # noqa: F403

DEBUG = False

import os

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "company-nt5o.onrender.com",
]

render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if render_hostname:
    ALLOWED_HOSTS.append(render_hostname)

# Fail fast if SECRET_KEY is left at dev default
if SECRET_KEY == "django-insecure-dev-only-change-in-production":  # noqa: F405
    raise ValueError(
        "Set SECRET_KEY in the environment for production deployments."
    )

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

# HTTPS: require secure cookies and (optionally) redirect HTTP → HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)  # noqa: F405

# HSTS: enable only when the site is served only over HTTPS (read Django docs before enabling).
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)  # noqa: F405
if SECURE_HSTS_SECONDS > 0:
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)  # noqa: F405
    SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)  # noqa: F405

# If behind a reverse proxy that sets X-Forwarded-Proto
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CORS_ALLOW_ALL_ORIGINS = False

# API: disable HTTP Basic auth unless explicitly enabled (reduces credential exposure over the wire).
if not env.bool("API_ENABLE_BASIC_AUTH", default=False):  # noqa: F405
    REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [  # noqa: F405
        "rest_framework.authentication.SessionAuthentication",
    ]

# Additional security headers for production
SECURE_SSL_HOST = env.str("SECURE_SSL_HOST", default=None)  # noqa: F405
SECURE_REDIRECT_EXEMPT = env.list("SECURE_REDIRECT_EXEMPT", default=[])  # noqa: F405



import os
import dj_database_url

DATABASES = {
    "default": dj_database_url.parse(
        os.environ.get("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True,
    )
}
CSRF_TRUSTED_ORIGINS = [
    "https://company-nt5o.onrender.com",
]