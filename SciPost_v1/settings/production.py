from .base import *

# THE MAIN THING HERE
DEBUG = False
CERTFILE = get_secret("CERTFILE")
ALLOWED_HOSTS = ['www.scipost.org', 'scipost.org']

# Static and media
STATIC_URL = 'https://scipost.org/static/'
STATIC_ROOT = '/home/jscaux/webapps/scipost_static/'
MEDIA_URL = 'https://scipost.org/media/'
MEDIA_ROOT = '/home/jscaux/webapps/scipost_media/'

# Recaptcha
RECAPTCHA_PUBLIC_KEY = get_secret("GOOGLE_RECAPTCHA_PUBLIC_KEY")
RECAPTCHA_PRIVATE_KEY = get_secret("GOOGLE_RECAPTCHA_PRIVATE_KEY")

WEBPACK_LOADER['DEFAULT']['CACHE'] = True
WEBPACK_LOADER['DEFAULT']['BUNDLE_DIR_NAME'] = '/home/jscaux/webapps/scipost_static/bundles/'

# Error reporting
ADMINS = MANAGERS = (('J.S.Caux', 'J.S.Caux@uva.nl'), ('J.de Wit', 'jorrandewit@outlook.com'))

# Cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = get_secret("EMAIL_HOST")
EMAIL_HOST_USER = get_secret("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = get_secret("EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL = 'admin@scipost.org'
SERVER_EMAIL = get_secret("SERVER_EMAIL")

# Other
CROSSREF_LOGIN_ID = get_secret("CROSSREF_LOGIN_ID")
CROSSREF_LOGIN_PASSWORD = get_secret("CROSSREF_LOGIN_PASSWORD")
DOAJ_API_KEY = get_secret("DOAJ_API_KEY")
HAYSTACK_CONNECTIONS['default']['PATH'] = '/home/jscaux/webapps/scipost/SciPost_v1/whoosh_index'
MAILCHIMP_API_USER = get_secret("MAILCHIMP_API_USER")
MAILCHIMP_API_KEY = get_secret("MAILCHIMP_API_KEY")

# iThenticate
ITHENTICATE_USERNAME = get_secret('ITHENTICATE_USERNAME')
ITHENTICATE_PASSWORD = get_secret('ITHENTICATE_PASSWORD')
