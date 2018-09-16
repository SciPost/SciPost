
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

from datetime import timedelta

from django.utils.translation import ugettext_lazy as _

from django.core.exceptions import ImproperlyConfigured
from django.contrib.messages import constants as message_constants

# Build paths inside the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# JSON-based secrets
secrets = json.load(open(os.path.join(BASE_DIR, "secrets.json")))


def get_secret(setting, secrets=secrets):
    """Get the secret variable or return explicit exception."""
    try:
        return secrets[setting]
    except KeyError:
        error_msg = "Set the {0} environment variable".format(setting)
        raise ImproperlyConfigured(error_msg)


SECRET_KEY = get_secret("SECRET_KEY")
CERTFILE = ''

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Secure proxy SSL header and secure cookies
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend'
    )

LOGIN_URL = '/login/'

GUARDIAN_RENDER_403 = True

# Session expire at browser close
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Wsgi scheme
os.environ['wsgi.url_scheme'] = 'https'

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_countries',
    'django_extensions',
    'django_mathjax',
    'ajax_select',
    'captcha',
    'guardian',
    'haystack',
    'rest_framework',
    'sphinxdoc',
    'affiliations',
    'colleges',
    'commentaries',
    'comments',
    'conflicts',
    'django_celery_results',
    'django_celery_beat',
    'finances',
    'guides',
    'invitations',
    'journals',
    'mails',
    'mailing_lists',
    'news',
    'notifications',
    'scipost',
    'submissions',
    'theses',
    'virtualmeetings',
    'proceedings',
    'production',
    'profiles',
    'partners',
    'preprints',
    'funders',
    'stats',
    'petitions',
    'webpack_loader'
)


HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': 'local_files/haystack/',
        'EXCLUDED_INDEXES': ['sphinxdoc.search_indexes.DocumentIndex'],
    },
}

# Brute force automatically re-index Haystack using post_save signals on all models.
# When write-traffic increases, a custom processor is preferred which only connects
# signals to eg. `vet-accepted` signals possibly using cron jobs instead of realtime updates.
HAYSTACK_SIGNAL_PROCESSOR = 'SciPost_v1.signalprocessors.AutoSearchIndexingProcessor'


SPHINXDOC_BASE_TEMPLATE = 'scipost/base.html'
SPHINXDOC_BUILD_DIR = '../build'
SPHINXDOC_PROTECTED_PROJECTS = {
    'developers': ['scipost.can_view_docs_scipost'],
}

CAPTCHA_CHALLENGE_FUNCT = 'captcha.helpers.math_challenge'
CAPTCHA_LETTER_ROTATION = (-15, 15)
CAPTCHA_NOISE_FUNCTIONS = ('captcha.helpers.noise_dots',)

SHELL_PLUS_POST_IMPORTS = (
    ('theses.factories', ('ThesisLinkFactory')),
    ('comments.factories', ('CommentFactory')),
    ('submissions.factories', ('SubmissionFactory', 'EICassignedSubmissionFactory')),
    ('commentaries.factories',
        ('EmptyCommentaryFactory',
         'CommentaryFactory',
         'UnvettedCommentaryFactory',
         'UnpublishedCommentaryFactory',)),
    ('scipost.factories', ('ContributorFactory')),
)

MATHJAX_ENABLED = True
MATHJAX_CONFIG_DATA = {
    "tex2jax": {
        "inlineMath": [['$', '$'], ['\\(', '\\)']],
        "processEscapes": True
        }
    }

MIDDLEWARE = (
    # 'django.middleware.http.ConditionalGetMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
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
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'SciPost_v1.wsgi.application'

# Messages
MESSAGE_TAGS = {
    message_constants.DEBUG: 'debug',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'danger',
}


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': get_secret("DB_NAME"),
        'USER': get_secret("DB_USER"),
        'PASSWORD': get_secret("DB_PWD"),
        'HOST': '127.0.0.1',
        'PORT': '5432'
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'
LANGUAGES = (
    ('en', _('English')),
)
LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)
TIME_ZONE = 'CET'

USE_I18N = True

USE_L10N = False
SHORT_DATE_FORMAT = DATE_FORMAT = 'Y-m-d'
DATETIME_FORMAT = 'Y-m-d H:i'

USE_TZ = True

# MEDIA
MEDIA_URL = '/media/'
MEDIA_URL_SECURE = '/files/secure/'
MAX_UPLOAD_SIZE = "1310720"  # Default max attachment size in Bytes

# -- These MEDIA settings are machine-dependent
MEDIA_ROOT = 'local_files/media/'
MEDIA_ROOT_SECURE = 'local_files/secure/media/'

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = 'local_files/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static_bundles'),
)

# Webpack handling the static bundles
WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': 'local_files/static/bundles/',
        'STATS_FILE': os.path.join(BASE_DIR, 'webpack-stats.json'),
        'POLL_INTERVAL': 0.1,
        'TIMEOUT': None,
        'IGNORE': ['.+\.hot-update.js', '.+\.map']
    }
}

# Email
EMAIL_BACKEND = 'mails.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = 'local_files/email/'
EMAIL_SUBJECT_PREFIX = '[SciPost Server] '
MAILCHIMP_DATABASE_CODE = 'us6'
MAILCHIMP_API_USER = 'test_API-user'
MAILCHIMP_API_KEY = 'test_API-key'


# iThenticate
ITHENTICATE_USERNAME = 'test_ithenticate_username'
ITHENTICATE_PASSWORD = 'test_ithenticate_password'

# Own settings
JOURNALS_DIR = 'journals'

CROSSREF_LOGIN_ID = ''
CROSSREF_LOGIN_PASSWORD = ''
CROSSREF_DEBUG = True
CROSSREF_DEPOSIT_EMAIL = 'techsupport@scipost.org'
DOAJ_API_KEY = ''

# Google reCaptcha with Google's global test keys
# https://developers.google.com/recaptcha/docs/faq#id-like-to-run-automated-tests-with-recaptcha-v2-what-should-i-do
RECAPTCHA_PUBLIC_KEY = '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'
RECAPTCHA_PRIVATE_KEY = '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe'
NOCAPTCHA = True


# PASSWORDS

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
]
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

CSRF_FAILURE_VIEW = 'scipost.views.csrf_failure'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s | %(message)s'
        },
    },
    'handlers': {
        'scipost_file_arxiv': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/path/to/logs/arxiv.log',
            'formatter': 'verbose',
        },
        'scipost_file_doi': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/path/to/logs/doi.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'scipost.services.arxiv': {
            'handlers': ['scipost_file_arxiv'],
            'level': 'INFO',
            'propagate': True,
            'formatter': 'simple',
        },
        'scipost.services.doi': {
            'handlers': ['scipost_file_doi'],
            'level': 'INFO',
            'propagate': True,
            'formatter': 'simple',
        },
    },
}

# Celery scheduled tasks
CELERY_RESULT_BACKEND = 'django-db'
CELERY_BROKER_URL = 'amqp://localhost'
CELERY_IMPORTS = ('submissions.tasks', )


# Automation.
ED_ASSIGMENT_DT_DELTA = timedelta(hours=12)
