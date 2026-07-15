"""
Django settings for PickleSphere - Pickleball Facility & Game Management System
"""

from pathlib import Path
import os
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Clean up empty env vars that would override .env values
# (System env vars with empty values take priority over .env via decouple)
for _key in ['EMAIL_BACKEND', 'EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_USE_TLS',
             'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD',
             'DEFAULT_FROM_EMAIL', 'DEFAULT_FROM_NAME']:
    if _key in os.environ and not os.environ[_key]:
        del os.environ[_key]


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# Generate a unique key: https://djecrety.ir/
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8001',
    'http://localhost:8001',
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    'axes',
    # PickleSphere Apps
    'accounts',
    'organizations',
    'courts',
    'reservations',
    'payments',
    'scoring',
    'notifications',
    'dashboard',
    'equipment',
    'tournaments',
    # Email
    'anymail',
    # Real-time
    'channels',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # django-axes must come after SessionMiddleware
    'axes.middleware.AxesMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'picklesphere.session_management.EnhancedSessionMiddleware',
    'picklesphere.session_management.SessionActivityMiddleware',
    # Auth Audit - logs unauthenticated access to potential unprotected views (DEBUG only)
    'dashboard.middleware.AuthAuditMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Maintenance Mode - blocks non-admin users when maintenance is active
    'dashboard.middleware.MaintenanceModeMiddleware',
]

ROOT_URLCONF = 'picklesphere.urls'

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
                'notifications.context_processors.notification_count',
                'notifications.sidebar_badge_context.sidebar_badges',
                'dashboard.context_processors.site_contact_info',
                'picklesphere.session_management.session_context_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'picklesphere.wsgi.application'
ASGI_APPLICATION = 'picklesphere.asgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Manila'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Authentication Settings
AUTHENTICATION_BACKENDS = [
    # django-axes must be first to track login attempts
    'axes.backends.AxesStandaloneBackend',
    'accounts.backends.EmailOrUsernameBackend',
    'django.contrib.auth.backends.ModelBackend',
]
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Session Management Settings
# Session timeout in seconds (30 minutes of inactivity)
SESSION_TIMEOUT = 1800
# Warning before timeout in seconds (5 minutes before)
SESSION_WARNING_BEFORE = 300
# Session cookie settings
SESSION_COOKIE_AGE = 3600  # 1 hour max session age
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
SESSION_COOKIE_SAMESITE = 'Lax'
# Save session on every request to track activity
SESSION_SAVE_EVERY_REQUEST = True
# Use database-backed sessions for reliability
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# ========== django-axes (Brute Force Protection) ==========
# Number of failed login attempts before lockout
AXES_FAILURE_LIMIT = 5
# Duration of lockout in hours (1 hour)
AXES_COOLOFF_TIME = 1
# Reset failure count after a successful login
AXES_RESET_ON_SUCCESS = True
# Use the custom email/username backend for attempt tracking
AXES_USERNAME_FORM_FIELD = 'username'
# Log attempts for auditing
AXES_ENABLE_ADMIN = True

# CSRF settings
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_HTTPONLY = False  # Must be False for JavaScript POST

# Stripe Payment Gateway Settings
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

# Email settings (configure in .env for production)
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@picklesphere.com')
DEFAULT_FROM_NAME = config('DEFAULT_FROM_NAME', default='PickleSphere')

# Anymail (Elastic Email) - Transactional email backend
ANYMAIL = {
    'ELASTICEMAIL_API_KEY': config('ELASTICEMAIL_API_KEY', default=''),
}
# When ELASTICEMAIL_API_KEY is set, switch to Elastic Email backend automatically
if config('ELASTICEMAIL_API_KEY', default=''):
    EMAIL_BACKEND = 'anymail.backends.elasticemail.ElasticEmailBackend'

# Site URL for email templates
SITE_URL = config('SITE_URL', default='http://localhost:8000')
SITE_NAME = 'PickleSphere'

# ========== REAL-TIME (Django Channels) ==========
# Channel layer configuration using Redis (or in-memory for dev)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}
# For production, use Redis:
# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels_redis.core.RedisChannelLayer',
#         'CONFIG': {
#             "hosts": [('127.0.0.1', 6379)],
#         },
#     },
# }


# ========== CACHE CONFIGURATION ==========
# Uses local memory cache by default (no Redis needed for dev)
# Cache timeout for CMS content (5 minutes = 300 seconds)
CMS_CACHE_TIMEOUT = config('CMS_CACHE_TIMEOUT', default=300, cast=int)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'picklesphere-cms',
        'TIMEOUT': CMS_CACHE_TIMEOUT,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        },
    },
    # Separate cache namespace for CMS to allow targeted flushing
    'cms': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'picklesphere-cms-content',
        'TIMEOUT': CMS_CACHE_TIMEOUT,
        'OPTIONS': {
            'MAX_ENTRIES': 200,
        },
    },
}
