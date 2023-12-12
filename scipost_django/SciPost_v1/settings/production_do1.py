import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

from .base import *

# THE MAIN THING HERE
DEBUG = False
ALLOWED_HOSTS = ["scipost.org", "www.scipost.org", "localhost", "142.93.224.252"]

# Static and media
STATIC_URL = "https://scipost.org/static/"
STATIC_ROOT = "/home/scipost/SciPost_static/static/"
MEDIA_URL = "https://scipost.org/media/"
MEDIA_ROOT = "/home/scipost/SciPost_media/media/"
MEDIA_ROOT_SECURE = "/home/scipost/local_files/secure/media/"
JOURNALS_DIR = "SCIPOST_JOURNALS"

# Secure storage for apimail
APIMAIL_MEDIA_ROOT_SECURE = "/home/scipost/local_files/secure/apimail/"

# Recaptcha
RECAPTCHA_PUBLIC_KEY = get_secret("GOOGLE_RECAPTCHA_PUBLIC_KEY")
RECAPTCHA_PRIVATE_KEY = get_secret("GOOGLE_RECAPTCHA_PRIVATE_KEY")

WEBPACK_LOADER["DEFAULT"]["CACHE"] = True
WEBPACK_LOADER["DEFAULT"]["BUNDLE_DIR_NAME"] = "/home/scipost/SciPost_static/bundles/"

# Error reporting
ADMINS = []
MANAGERS = (("J.S.Caux", "J.S.Caux@uva.nl"),)

# Cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Email
EMAIL_BACKEND = "mails.backends.filebased.ModelEmailBackend"
EMAIL_BACKEND_ORIGINAL = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = get_secret("EMAIL_HOST")
EMAIL_HOST_USER = get_secret("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = get_secret("EMAIL_HOST_PASSWORD")
EMAIL_PORT = 587

DEFAULT_FROM_EMAIL = "admin@scipost.org"
SERVER_EMAIL = get_secret("SERVER_EMAIL")

# Other
CROSSREF_LOGIN_ID = get_secret("CROSSREF_LOGIN_ID")
CROSSREF_LOGIN_PASSWORD = get_secret("CROSSREF_LOGIN_PASSWORD")
CROSSREF_DEBUG = False
CROSSREF_DEPOSIT_EMAIL = "edadmin@scipost.org"

DOAJ_API_KEY = get_secret("DOAJ_API_KEY")
HAYSTACK_CONNECTIONS["default"]["PATH"] = "/home/scipost/SciPost/whoosh_index"

# iThenticate
ITHENTICATE_USERNAME = get_secret("ITHENTICATE_USERNAME")
ITHENTICATE_PASSWORD = get_secret("ITHENTICATE_PASSWORD")

# Logging
LOGGING["handlers"]["scipost_file_arxiv"][
    "filename"
] = "/home/scipost/SciPost_logs/arxiv.log"
LOGGING["handlers"]["scipost_file_doi"][
    "filename"
] = "/home/scipost/SciPost_logs/doi.log"
LOGGING["handlers"]["api_file"]["filename"] = "/home/scipost/SciPost_logs/api.log"
LOGGING["handlers"]["oauth_file"]["filename"] = "/home/scipost/SciPost_logs/oauth.log"
LOGGING["handlers"]["submission_fellowship_updates"][
    "filename"
] = "/home/scipost/SciPost_logs/submission_fellowship_updates.log"


# API
# REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = ('rest_framework.renderers.JSONRenderer',)

# Mailgun credentials
MAILGUN_API_KEY = get_secret("MAILGUN_API_KEY")

# Sentry
sentry_sdk.init(
    dsn=get_secret("SENTRY_DSN"),
    integrations=[DjangoIntegration(), CeleryIntegration()],
    enable_tracing=True,
)
CSP_REPORT_URI = get_secret("CSP_SENTRY")
CSP_REPORT_ONLY = False


# CORS headers
CORS_ALLOWED_ORIGINS = [
    "https://git.scipost.org",
]

# GitLab API
GITLAB_ROOT = "SciPost"
GITLAB_URL = "git.scipost.org"
GITLAB_KEY = get_secret("GITLAB_KEY")
