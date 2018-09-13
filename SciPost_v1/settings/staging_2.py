# Used on staging server with IP 128.199.54.82

from .base import *

# THE MAIN THING HERE
DEBUG = False
ALLOWED_HOSTS = ['128.199.54.82']

# Static and media
STATIC_ROOT = '/home/scipost_static/static/'
MEDIA_ROOT = '/home/scipost_media/static/'

# Webpack
WEBPACK_LOADER['DEFAULT']['CACHE'] = True
WEBPACK_LOADER['DEFAULT']['BUNDLE_DIR_NAME'] = '/home/scipost/scipost_static/bundles/'

# ReCaptcha keys
RECAPTCHA_PUBLIC_KEY = get_secret("GOOGLE_RECAPTCHA_PUBLIC_KEY")
RECAPTCHA_PRIVATE_KEY = get_secret("GOOGLE_RECAPTCHA_PRIVATE_KEY")

# Logging location
LOGGING['handlers']['scipost_file_arxiv']['filename'] = '/home/scipost/logs/arxiv.log'
LOGGING['handlers']['scipost_file_doi']['filename'] = '/home/scipost/logs/doi.log'

# Cookies
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Email
EMAIL_BACKEND = 'mails.backends.filebased.ModelEmailBackend'
EMAIL_BACKEND_ORIGINAL = 'django.core.mail.backends.dummy.EmailBackend'  # Disable real processing
