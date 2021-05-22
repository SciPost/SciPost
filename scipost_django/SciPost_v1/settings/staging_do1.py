# Used on staging server (on Digital Ocean droplet) with IP 157.245.73.188

from .base import *

# THE MAIN THING HERE
DEBUG = False
ALLOWED_HOSTS = ['www.scipost-staging.org', 'scipost-staging.org']

# Static and media
STATIC_ROOT = '/home/scipost/SciPost/static/'
MEDIA_ROOT = '/home/scipost/SciPost/media/'

# Webpack
WEBPACK_LOADER['DEFAULT']['CACHE'] = True
WEBPACK_LOADER['DEFAULT']['BUNDLE_DIR_NAME'] = '/home/scipost/SciPost/static_bundles/bundles/'

# ReCaptcha keys
#RECAPTCHA_PUBLIC_KEY = get_secret("GOOGLE_RECAPTCHA_PUBLIC_KEY")
#RECAPTCHA_PRIVATE_KEY = get_secret("GOOGLE_RECAPTCHA_PRIVATE_KEY")

# Logging location
LOGGING['handlers']['scipost_file_arxiv']['filename'] = '/home/scipost/SciPost/local_files/logs/arxiv.log'
LOGGING['handlers']['scipost_file_doi']['filename'] = '/home/scipost/SciPost/local_files/logs/doi.log'
LOGGING['handlers']['api_file']['filename'] = '/home/scipost/SciPost/local_files/logs/api.log'
LOGGING['handlers']['oauth_file']['filename'] = '/home/scipost/SciPost/local_files/logs/oauth.log'

# Cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Email
EMAIL_BACKEND = 'mails.backends.filebased.ModelEmailBackend'
EMAIL_BACKEND_ORIGINAL = 'django.core.mail.backends.dummy.EmailBackend'  # Disable real processing

WSGI_APPLICATION = 'SciPost_v1.wsgi_staging_do1.application'

# Mongo
#MONGO_DATABASE['user'] = get_secret('MONGO_DB_USER')
#MONGO_DATABASE['password'] = get_secret('MONGO_DB_PASSWORD')
#MONGO_DATABASE['port'] = get_secret('MONGO_DB_PORT')

# Mailgun credentials
MAILGUN_API_KEY = get_secret('MAILGUN_API_KEY')
