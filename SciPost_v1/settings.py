"""
Django settings for SciPost_v1 project.

Generated by 'django-admin startproject' using Django 1.8.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

host_settings_path = os.path.join(os.path.dirname(BASE_DIR),"scipost-host-settings.json")
host_settings = json.load(open(host_settings_path))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = host_settings["SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = host_settings["DEBUG"]

ALLOWED_HOSTS = []

# Secure proxy SSL header and secure cookies                                                       
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = host_settings["SESSION_COOKIE_SECURE"]
CSRF_COOKIE_SECURE = host_settings["CSRF_COOKIE_SECURE"]

# Session expire at browser close                                                                  
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Wsgi scheme                                                                                      
os.environ['wsgi.url_scheme'] = 'https'

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_mathjax',
    'commentaries',
    'comments',
    'contributors',
    'journals',
    'ratings',
    'reports',
    'scipost',
    'submissions',
)

MATHJAX_ENABLED = True
MATHJAX_CONFIG_DATA = {
    "tex2jax": {
        "inlineMath": [['$', '$'], ['\\(', '\\)']],
        "processEscapes": True
        }
    }

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'SciPost_v1.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'SciPost_v1.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': host_settings["DB_NAME"],
        'USER': host_settings["DB_USER"],
        'PASSWORD': host_settings["DB_PWD"],
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'CET'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = host_settings["STATIC_URL"]
STATIC_ROOT = host_settings["STATIC_ROOT"]

# Email
EMAIL_BACKEND = host_settings["EMAIL_BACKEND"]
EMAIL_FILE_PATH = host_settings["EMAIL_FILE_PATH"]
EMAIL_HOST = host_settings["EMAIL_HOST"]
EMAIL_HOST_USER = host_settings["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = host_settings["EMAIL_HOST_PASSWORD"]
DEFAULT_FROM_EMAIL = host_settings["DEFAULT_FROM_EMAIL"]
SERVER_EMAIL = host_settings["SERVER_EMAIL"]
