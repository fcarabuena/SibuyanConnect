"""
SibuyanConnect settings.

Everything is configured from environment variables so the same code runs on a
laptop (SQLite, console email) and on a free host (Render / PythonAnywhere).
No setting here requires a paid service.
"""
import os
from pathlib import Path

import dj_database_url
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes", "on")


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
CSRF_TRUSTED_ORIGINS = [o for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o]

INSTALLED_APPS = [
    # modeltranslation must come before django.contrib.admin
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "django.contrib.syndication",
    "core",
    "services",
    "programs",
    "concerns",
    "news",
    "tourism",
    "transport",
    "emergency",
    "marketplace",
    "civic",
    "assistant",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "core.middleware.SiteLanguageMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "sibuyanconnect.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "core.context_processors.site_context",
            ],
        },
    },
]

WSGI_APPLICATION = "sibuyanconnect.wsgi.application"

# SQLite for local development; set DATABASE_URL=postgres://... in production.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}", conn_max_age=600
    )
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
FIXTURE_DIRS = [BASE_DIR / "fixtures"]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "concerns:mine"
LOGOUT_REDIRECT_URL = "home"

# --- Internationalisation ---------------------------------------------------
# Romblomanon has no two-letter ISO 639-1 code, so we use its ISO 639-3 code.
LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", _("English")),
    ("fil", _("Filipino")),
    ("rol", _("Romblomanon")),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "Asia/Manila"
USE_I18N = True
USE_TZ = True

MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
MODELTRANSLATION_FALLBACK_LANGUAGES = ("en",)

# --- Static & media ---------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        if DEBUG
        else "whitenoise.storage.CompressedStaticFilesStorage"
    },
}

# Uploaded photos are resized/compressed with Pillow before saving.
IMAGE_MAX_DIMENSION = 1280
IMAGE_JPEG_QUALITY = 70
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024

# --- Email (free: console in dev, any SMTP account in production) -----------
EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", "SibuyanConnect <no-reply@sibuyanconnect.local>"
)

# --- Optional SMS (off by default: SMS gateways cost money) ------------------
# Dotted path to a callable(phone, message). Leave empty to disable.
SMS_BACKEND = os.environ.get("SMS_BACKEND", "")

# --- Help assistant ---------------------------------------------------------
# Layer 1 (FAQ / site search) is always on. Layer 2 is optional:
#   "none"   - no LLM; unanswered questions are handed off to staff
#   "gemini" - Google Gemini API free tier (needs a free GEMINI_API_KEY)
#   "ollama" - self-hosted open model at OLLAMA_URL
ASSISTANT_LLM_BACKEND = os.environ.get("ASSISTANT_LLM_BACKEND", "none")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

# Sibuyan Island centre, used for the Open-Meteo weather widget (no API key).
WEATHER_LAT = 12.42
WEATHER_LON = 122.57

# --- Security hardening when not in debug -----------------------------------
SESSION_COOKIE_HTTPONLY = True
# OpenStreetMap's tile servers reject requests without a Referer. Django's default
# ("same-origin") strips it on cross-site requests; this sends only our origin
# (never the path, so no ticket links leak) to other sites, and only over HTTPS.
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 3600
    SECURE_CONTENT_TYPE_NOSNIFF = True
