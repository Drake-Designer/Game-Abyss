"""
Django settings for core project.
"""

from importlib import import_module
from pathlib import Path
import os
import sys
import warnings

import dj_database_url  # For Postgres when DATABASE_URL is set

# Load env.py if present (it may set os.environ via side effects)
try:
    import_module("env")  # pragma: no cover
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Base paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Test detection
# ---------------------------------------------------------------------------

RUNNING_TESTS = len(sys.argv) > 1 and sys.argv[1] == "test"

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    if RUNNING_TESTS:
        SECRET_KEY = "django-insecure-test-key"
    else:
        raise RuntimeError(
            "SECRET_KEY is not set. Put it in env.py or in your hosting config vars."
        )

DEBUG = os.environ.get("DEBUG", "True") == "True"

_alh = os.environ.get("ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [h.strip() for h in _alh.split(",") if h.strip()]

_cto = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _cto.split(",") if o.strip()]

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # Third-party
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "widget_tweaks",
    # Local apps
    "core",
    "pages",
    "accounts",
    "blog",
    "gallery",
]

SITE_ID = int(os.environ.get("SITE_ID", "1"))

# ---------------------------------------------------------------------------
# Middleware and URLs
# ---------------------------------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # Enable when you do not need responsive screenshots inside iframes
    # "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

db_url = os.environ.get("DATABASE_URL")
if db_url:
    DATABASES["default"] = dj_database_url.parse(
        db_url,
        conn_max_age=600,
        ssl_require=True,
    )

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# I18N and TZ
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/Dublin"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static and media
# ---------------------------------------------------------------------------

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Whitenoise for static files in production
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_USE_FINDERS = True

# Django 5 storage API
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            STATICFILES_STORAGE
            if not RUNNING_TESTS
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Allauth
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https" if not DEBUG else "http"
ACCOUNT_LOGIN_METHODS = {"email", "username"}
ACCOUNT_SIGNUP_FIELDS = ["email", "username*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
LOGIN_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"
ACCOUNT_EMAIL_SUBJECT_PREFIX = "[Game Abyss] "

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    "Game Abyss <team.gameabyss@gmail.com>",
)

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
PRIMARY_SUPERADMIN_EMAIL = os.environ.get(
    "PRIMARY_SUPERADMIN_EMAIL",
    "team.gameabyss@gmail.com",
)

if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = os.environ.get(
        "EMAIL_BACKEND",
        "django.core.mail.backends.smtp.EmailBackend",
    )
    EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.sendgrid.net")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "apikey")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")

SERVER_EMAIL = DEFAULT_FROM_EMAIL

# ---------------------------------------------------------------------------
# App defaults
# ---------------------------------------------------------------------------

_banned_words_raw = os.environ.get(
    "BLOG_COMMENT_BANNED_WORDS",
    "spam, scam, offensive",
)
BLOG_COMMENT_BANNED_WORDS = [
    w.strip().lower() for w in _banned_words_raw.split(",") if w.strip()
]
BLOG_COMMENT_MAX_LINKS = int(os.environ.get("BLOG_COMMENT_MAX_LINKS", "2"))

# Allow friendly iframes when needed (e.g., screenshot tools)
X_FRAME_OPTIONS = "SAMEORIGIN"

# ---------------------------------------------------------------------------
# Cloudinary (optional)
# ---------------------------------------------------------------------------

try:
    import cloudinary  # type: ignore
except ImportError:
    cloudinary = None  # type: ignore

USE_CLOUDINARY = False
if cloudinary is not None:
    cloudinary_url = os.environ.get("CLOUDINARY_URL")
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME")
    api_key = os.environ.get("CLOUDINARY_API_KEY")
    api_secret = os.environ.get("CLOUDINARY_API_SECRET")

    if cloudinary_url:
        cloudinary.config(cloudinary_url=cloudinary_url, secure=True)
        USE_CLOUDINARY = True
    elif cloud_name and api_key and api_secret:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )
        USE_CLOUDINARY = True
    else:
        warnings.warn(
            "Cloudinary credentials are not configured. Set CLOUDINARY_URL or "
            "CLOUDINARY_CLOUD_NAME/API_KEY/API_SECRET to enable image uploads.",
            RuntimeWarning,
        )
else:
    warnings.warn(
        "Cloudinary package is not installed. Falling back to default file storage.",
        RuntimeWarning,
    )

if USE_CLOUDINARY:
    INSTALLED_APPS.extend(["cloudinary", "cloudinary_storage"])
    STORAGES["default"]["BACKEND"] = (
        "cloudinary_storage.storage.MediaCloudinaryStorage"
    )
    # Keep legacy var for compatibility with some third-party apps
    DEFAULT_FILE_STORAGE = STORAGES["default"]["BACKEND"]
