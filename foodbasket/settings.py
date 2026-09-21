from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-foodbasket-secret-key-change-in-production')

DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1')

allowed = os.environ.get('ALLOWED_HOSTS')
if allowed:
    ALLOWED_HOSTS = [h.strip() for h in allowed.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['*'] if DEBUG else ['localhost', '127.0.0.1', '.onrender.com']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'store',
]

try:
    import whitenoise
    HAS_WHITENOISE = True
except ImportError:
    HAS_WHITENOISE = False

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
]
if HAS_WHITENOISE:
    MIDDLEWARE.append('whitenoise.middleware.WhiteNoiseMiddleware')

MIDDLEWARE.extend([
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
])

ROOT_URLCONF = 'foodbasket.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'store.context_processors.cart_count',
                'store.context_processors.delivery_location',
            ],
        },
    },
]

WSGI_APPLICATION = 'foodbasket.wsgi.application'

import logging
import socket
import urllib.parse

from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

db_url = os.environ.get('DATABASE_URL')


def check_postgresql_connection(host, port, db_name, user, password, options=None, timeout=2):
    """Verifies that a PostgreSQL host is reachable and accepts SSL/TCP connections."""
    try:
        import psycopg2
        conn_params = {
            'dbname': db_name,
            'user': user,
            'password': password,
            'host': host,
            'port': port or 5432,
            'connect_timeout': int(timeout),
        }
        if options and 'sslmode' in options:
            conn_params['sslmode'] = options['sslmode']
        conn = psycopg2.connect(**conn_params)
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


if db_url:
    url = urllib.parse.urlparse(db_url)
    raw_host = url.hostname
    port = url.port or 5432
    db_name = url.path[1:]
    user = url.username
    password = url.password

    db_options = {}
    if 'sslmode' in (url.query or ''):
        params = urllib.parse.parse_qs(url.query)
        if 'sslmode' in params:
            db_options['sslmode'] = params['sslmode'][0]
    elif not DEBUG or (raw_host and '.render.com' in raw_host):
        db_options['sslmode'] = 'require'

    candidates = []
    if raw_host:
        candidates.append(raw_host)
        if raw_host.startswith('dpg-') and '.' not in raw_host:
            candidates.append(f"{raw_host}.oregon-postgres.render.com")

    connected_host = None
    connection_error = None

    for candidate in candidates:
        try:
            socket.getaddrinfo(candidate, port)
        except Exception:
            continue

        is_ok, err = check_postgresql_connection(
            host=candidate,
            port=port,
            db_name=db_name,
            user=user,
            password=password,
            options=db_options,
            timeout=2,
        )
        if is_ok:
            connected_host = candidate
            logger.info(f"Connected to PostgreSQL database at {connected_host}:{port}/{db_name}")
            break
        else:
            connection_error = err

    if connected_host:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': db_name,
                'USER': user,
                'PASSWORD': password,
                'HOST': connected_host,
                'PORT': port,
                'OPTIONS': db_options,
            }
        }
    else:
        allow_fallback = os.environ.get('ALLOW_SQLITE_FALLBACK', 'true').lower() in ('true', '1')
        if allow_fallback or DEBUG:
            logger.warning(
                f"PostgreSQL connection to host '{raw_host}' failed: {connection_error}. "
                f"Falling back to SQLite at {BASE_DIR / 'db.sqlite3'}. "
                f"To use PostgreSQL on Render, ensure the database is active and use the External Database URL."
            )
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': BASE_DIR / 'db.sqlite3',
                }
            }
        else:
            raise ImproperlyConfigured(
                f"PostgreSQL connection to host '{raw_host}' failed: {connection_error}. "
                f"Please verify your database is running or set ALLOW_SQLITE_FALLBACK=True."
            )
else:
    if not DEBUG and os.environ.get('ALLOW_SQLITE_FALLBACK', 'true').lower() not in ('true', '1'):
        raise ImproperlyConfigured("DATABASE_URL environment variable is required in production.")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Razorpay credentials
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_placeholder')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'secret_placeholder')

# Production Security
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() in ('true', '1')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', 31536000))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# Logging configuration
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/django.log',
            'maxBytes': 1024 * 1024 * 5, # 5MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Sentry integration
sentry_dsn = os.environ.get('SENTRY_DSN')
if sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[DjangoIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=True
    )

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage" if HAS_WHITENOISE else "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Email settings
if os.environ.get('PRODUCTION') or os.environ.get('SENDGRID_API_KEY') or os.environ.get('EMAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.sendgrid.net')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'apikey')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@foodbasket.com')
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'noreply@foodbasket.com'

# Razorpay Payment Gateway Settings
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')

# Real-Time Geocoding Provider Settings
# Supported providers: 'nominatim', 'opencage', 'google', 'mapbox', 'here'
GEOCODING_PROVIDER = os.environ.get('GEOCODING_PROVIDER', 'nominatim').lower().strip()
GEOCODING_API_KEY = os.environ.get('GEOCODING_API_KEY', '').strip()

