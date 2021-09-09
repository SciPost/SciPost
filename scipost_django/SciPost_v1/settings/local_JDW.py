from .base import *

import os

LOCAL_DATA_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) + '/data'

# THE MAIN THING HERE
DEBUG = True

# Static and media
STATIC_ROOT = LOCAL_DATA_PATH + '/static/'
MEDIA_ROOT = LOCAL_DATA_PATH + '/media/'
WEBPACK_LOADER['DEFAULT']['BUNDLE_DIR_NAME'] = LOCAL_DATA_PATH + '/static/bundles/'

# CROSSREF_LOGIN_ID = get_secret("CROSSREF_LOGIN_ID")
# CROSSREF_LOGIN_PASSWORD = get_secret("CROSSREF_LOGIN_PASSWORD")
CROSSREF_DEBUG = True
CROSSREF_DEPOSIT_EMAIL = 'jorrandewit@outlook.com'

# MAILCHIMP_API_USER = get_secret("MAILCHIMP_API_USER")
# MAILCHIMP_API_KEY = get_secret("MAILCHIMP_API_KEY")

# Logging
LOGGING['handlers']['scipost_file_arxiv']['filename'] = LOCAL_DATA_PATH + '/logs/arxiv.log'
LOGGING['handlers']['scipost_file_doi']['filename'] = LOCAL_DATA_PATH + '/logs/doi.log'
LOGGING['handlers']['api_file']['filename'] = LOCAL_DATA_PATH + '/logs/api.log'
LOGGING['handlers']['oauth_file']['filename'] = LOCAL_DATA_PATH + '/logs/oauth.log'

# Customized mailbackend
EMAIL_BACKEND = "mails.backends.filebased.ModelEmailBackend"
EMAIL_BACKEND_ORIGINAL = "mails.backends.filebased.EmailBackend"

# # CSP
# CSP_REPORT_URI = get_secret('CSP_SENTRY')
# CSP_REPORT_ONLY = True

# # Mailgun credentials
# MAILGUN_API_KEY = get_secret('MAILGUN_API_KEY')

# CORS headers
CORS_ALLOW_ALL_ORIGINS = True # Dev only!
