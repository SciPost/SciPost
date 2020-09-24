import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

from .base import *

# THE MAIN THING HERE
DEBUG = False
ALLOWED_HOSTS = ['www.scipost.org', 'scipost.org']

# Static and media
STATIC_URL = 'https://scipost.org/static/'
STATIC_ROOT = '/home/scipost/webapps/scipost_static/'
MEDIA_URL = 'https://scipost.org/media/'
MEDIA_ROOT = '/home/scipost/webapps/scipost_media/'
JOURNALS_DIR = 'SCIPOST_JOURNALS'

# Recaptcha
RECAPTCHA_PUBLIC_KEY = get_secret("GOOGLE_RECAPTCHA_PUBLIC_KEY")
RECAPTCHA_PRIVATE_KEY = get_secret("GOOGLE_RECAPTCHA_PRIVATE_KEY")

WEBPACK_LOADER['DEFAULT']['CACHE'] = True
WEBPACK_LOADER['DEFAULT']['BUNDLE_DIR_NAME'] = '/home/scipost/webapps/scipost_static/bundles/'

# Error reporting
ADMINS = []
MANAGERS = (('J.S.Caux', 'J.S.Caux@uva.nl'), ('J.de Wit', 'jorrandewit@outlook.com'))

# Cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Email
EMAIL_BACKEND = 'mails.backends.filebased.ModelEmailBackend'
EMAIL_BACKEND_ORIGINAL = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = get_secret("EMAIL_HOST")
EMAIL_HOST_USER = get_secret("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = get_secret("EMAIL_HOST_PASSWORD")
EMAIL_PORT = 587

DEFAULT_FROM_EMAIL = 'admin@scipost.org'
SERVER_EMAIL = get_secret("SERVER_EMAIL")

# Other
CROSSREF_LOGIN_ID = get_secret("CROSSREF_LOGIN_ID")
CROSSREF_LOGIN_PASSWORD = get_secret("CROSSREF_LOGIN_PASSWORD")
CROSSREF_DEBUG = False
CROSSREF_DEPOSIT_EMAIL = 'edadmin@scipost.org'

DOAJ_API_KEY = get_secret("DOAJ_API_KEY")
HAYSTACK_CONNECTIONS['default']['PATH'] = '/home/scipost/webapps/scipost_py38/SciPost/whoosh_index'
MAILCHIMP_API_USER = get_secret("MAILCHIMP_API_USER")
MAILCHIMP_API_KEY = get_secret("MAILCHIMP_API_KEY")

# iThenticate
ITHENTICATE_USERNAME = get_secret('ITHENTICATE_USERNAME')
ITHENTICATE_PASSWORD = get_secret('ITHENTICATE_PASSWORD')

# Logging
LOGGING['handlers']['scipost_file_arxiv']['filename'] = '/home/scipost/webapps/scipost_py38/logs/arxiv.log'
LOGGING['handlers']['scipost_file_doi']['filename'] = '/home/scipost/webapps/scipost_py38/logs/doi.log'
LOGGING['handlers']['api_file']['filename'] = '/home/scipost/webapps/scipost_py38/logs/api.log'
LOGGING['handlers']['oauth_file']['filename'] = '/home/scipost/webapps/scipost_py38/logs/oauth.log'


# API
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = ('rest_framework.renderers.JSONRenderer',)


# Sentry
sentry_sdk.init(
    dsn=get_secret('SENTRY_DSN'),
    integrations=[DjangoIntegration(), CeleryIntegration()]
)
CSP_REPORT_URI = get_secret('CSP_SENTRY')
CSP_REPORT_ONLY = False
