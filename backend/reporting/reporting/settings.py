"""
Django settings for reporting project.

Generated by 'django-admin startproject' using Django 3.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
import tempfile
import sys
from pathlib import Path
from .site_settings import production

import sqlalchemy_utils

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FRONTEND_DIR = Path(BASE_DIR).parent.parent / 'frontend'

STATICFILES_DIRS = [
    os.path.join(FRONTEND_DIR, 'dist/static'),
]

if True:
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'azn@lvr77l5%_yj=zylpj6-8abzm!g)p0zy+7*#vgm=k79w4+f'

GTA_API_USER = "aobolens-api"
GTA_API_PASSWORD = "BDD1D46EB3E6C044F536BC150E074B886B6A12AE741F00EFAA0649660B8A44DF"

EMAIL_HOST = 'smtp.intel.com'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = not production

ALLOWED_HOSTS = ['*']
INTERNAL_IPS = ['127.0.0.1', '10.125.50.240']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_dramatiq',

    'rest_framework',
    'rest_framework_tracking',

    'api.apps.ApiConfig',
    'api.collate.apps.ImportConfig',
    'test_verifier.apps.TestVerifierConfig',
    'debug_toolbar',
    'rest_framework_swagger',
    'webpack_loader',
    'corsheaders',
    'aldjemy',
    'django_filters'
]
CORS_ORIGIN_ALLOW_ALL = True

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'sso.middleware.RemoteUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend', 'rest_framework.filters.OrderingFilter'],
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema'
}

ROOT_URLCONF = 'reporting.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'reporting.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'NAME': 'reporting_db',
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'localhost',
        'USER': 'psql_user',
        'PASSWORD': 'password'
    }
}

# Use sqlite in-memory database for testing
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'TEST_CHARSET': 'UTF8',
        'NAME': ':memory:',
        'TEST_NAME': ':memory:',
    }


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = []

AUTH_USER_MODEL = 'auth.User'   # default

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]
if production:
    AUTHENTICATION_BACKENDS.append('sso.backends.RemoteUserBackend')

INTEL_LDAP_USERNAME = os.getenv('INTEL_LDAP_USERNAME')
INTEL_LDAP_PASSWORD = os.getenv('INTEL_LDAP_PASSWORD')

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/media/'

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': DEBUG,
        'BUNDLE_DIR_NAME': '/bundles/',
        'STATS_FILE': os.path.join(FRONTEND_DIR, 'webpack-stats.json'),
    }
}

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbosed': {
            'class': 'logging.Formatter',
            'format': '%(levelname)-5s [%(asctime)-15s] [%(module)s:%(funcName)s:%(lineno)d] %(message)s',
        },
        'brief': {
            'class': 'logging.Formatter',
            'format': '%(levelname)-5s [%(asctime)-15s] %(message)s',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': ('verbosed' if DEBUG else 'brief'),
        },
    },
    'loggers': {
        'api': {
            'handlers': ['console'],
            'propagate': False,
            'level': ('DEBUG' if DEBUG else 'INFO'),
        },
        'django_dramatiq': {
            'handlers': ['console'],
            'propagate': False,
            'level': ('DEBUG' if DEBUG else 'INFO'),
        },
        'django': {
            'handlers': ['console'],
            'propagate': False,
            'level': 'INFO',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

# Tasks
DRAMATIQ_REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
DRAMATIQ_BROKER = {
    "BROKER": "dramatiq.brokers.redis.RedisBroker",
    "OPTIONS": {
        "url": DRAMATIQ_REDIS_URL,
    },

    "MIDDLEWARE": [
        "dramatiq.middleware.AgeLimit",
        "dramatiq.middleware.TimeLimit",
        "dramatiq.middleware.Callbacks",
        "dramatiq.middleware.Retries",
        "django_dramatiq.middleware.AdminMiddleware",
        "django_dramatiq.middleware.DbConnectionsMiddleware",
    ]
}


def uuid_field(field):
    return sqlalchemy_utils.UUIDType()

ALDJEMY_DATA_TYPES = {
    "UUIDField": uuid_field
}

MEDIA_ROOT = tempfile.gettempdir()
