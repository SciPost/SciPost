from .base import *

# THE MAIN THING HERE
DEBUG = True

# Static and media
STATIC_ROOT = '/home/jscaux/SciPost/sites/scipost.org/SciPost/local_files/static/'
MEDIA_ROOT = '/home/jscaux/SciPost/sites/scipost.org/SciPost/local_files/media/'
WEBPACK_LOADER['DEFAULT']['BUNDLE_DIR_NAME'] =\
    '/home/jscaux/SciPost/sites/scipost.org/SciPost/local_files/static/bundles/'

CROSSREF_LOGIN_ID = get_secret("CROSSREF_LOGIN_ID")
CROSSREF_LOGIN_PASSWORD = get_secret("CROSSREF_LOGIN_PASSWORD")
CROSSREF_DEBUG = True
CROSSREF_DEPOSIT_EMAIL = 'edadmin@scipost.org'

MAILCHIMP_API_USER = get_secret("MAILCHIMP_API_USER")
MAILCHIMP_API_KEY = get_secret("MAILCHIMP_API_KEY")

# Logging
LOGGING['handlers']['scipost_file_arxiv']['filename'] = '/home/jscaux/SciPost/sites/scipost.org/SciPost/local_files/logs/arxiv.log'
LOGGING['handlers']['scipost_file_doi']['filename'] = '/home/jscaux/SciPost/sites/scipost.org/SciPost/local_files/logs/doi.log'
LOGGING['handlers']['api_file']['filename'] = '/home/jscaux/SciPost/sites/scipost.org/SciPost/local_files/logs/api.log'
LOGGING['handlers']['oauth_file']['filename'] = '/home/jscaux/SciPost/sites/scipost.org/SciPost/local_files/logs/oauth.log'

CROSSREF_DEPOSIT_EMAIL = 'jscaux@scipost.org'

# Customized mailbackend
EMAIL_BACKEND = "mails.backends.filebased.ModelEmailBackend"
EMAIL_BACKEND_ORIGINAL = "mails.backends.filebased.EmailBackend"

# CSP
CSP_REPORT_URI = get_secret('CSP_SENTRY')
CSP_REPORT_ONLY = True

# Mailgun credentials
MAILGUN_API_KEY = get_secret('MAILGUN_API_KEY')

# CORS headers
CORS_ALLOW_ALL_ORIGINS = True # Dev only!