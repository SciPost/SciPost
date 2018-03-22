from .base import *

# THE MAIN THING HERE
DEBUG = True

# Debug toolbar settings
INSTALLED_APPS += (
    'debug_toolbar',
)
MIDDLEWARE += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)
INTERNAL_IPS = ['127.0.0.1', '::1']

# Static and media
STATIC_ROOT = '/Users/jorrandewit/Documents/Develop/SciPost/scipost_v1/local_files/static/'
MEDIA_ROOT = '/Users/jorrandewit/Documents/Develop/SciPost/scipost_v1/local_files/media/'
WEBPACK_LOADER['DEFAULT']['BUNDLE_DIR_NAME'] =\
    '/Users/jorrandewit/Documents/Develop/SciPost/scipost_v1/local_files/static/bundles/'

MAILCHIMP_API_USER = get_secret("MAILCHIMP_API_USER")
MAILCHIMP_API_KEY = get_secret("MAILCHIMP_API_KEY")

DATABASES['default']['PORT'] = '5433'

# iThenticate
ITHENTICATE_USERNAME = get_secret('ITHENTICATE_USERNAME')
ITHENTICATE_PASSWORD = get_secret('ITHENTICATE_PASSWORD')

# Logging
LOGGING['handlers']['scipost_file_arxiv']['filename'] = '/Users/jorrandewit/Documents/Develop/SciPost/scipost_v1/logs/arxiv.log'
LOGGING['handlers']['scipost_file_doi']['filename'] = '/Users/jorrandewit/Documents/Develop/SciPost/scipost_v1/logs/doi.log'

# Other
CROSSREF_LOGIN_ID = get_secret("CROSSREF_LOGIN_ID")
CROSSREF_LOGIN_PASSWORD = get_secret("CROSSREF_LOGIN_PASSWORD")
CROSSREF_DEPOSIT_EMAIL = 'jorrandewit@scipost.org'
