from .base import *

# THE MAIN THING HERE
DEBUG = True

# Static and media
STATIC_ROOT = '/Users/jscaux/Sites/SciPost.org/scipost_v1/local_files/static/'
MEDIA_ROOT = '/Users/jscaux/Sites/SciPost.org/scipost_v1/local_files/media/'
WEBPACK_LOADER['DEFAULT']['BUNDLE_DIR_NAME'] =\
    '/Users/jscaux/Sites/SciPost.org/scipost_v1/local_files/static/bundles/'

CROSSREF_LOGIN_ID = get_secret("CROSSREF_LOGIN_ID")
CROSSREF_LOGIN_PASSWORD = get_secret("CROSSREF_LOGIN_PASSWORD")
CROSSREF_DEBUG = False
CROSSREF_DEPOSIT_EMAIL = 'edadmin@scipost.org'

MAILCHIMP_API_USER = get_secret("MAILCHIMP_API_USER")
MAILCHIMP_API_KEY = get_secret("MAILCHIMP_API_KEY")

# Logging
LOGGING['handlers']['scipost_file_arxiv']['filename'] = '/Users/jscaux/Sites/SciPost.org/scipost_v1/local_files/logs/arxiv.log'
LOGGING['handlers']['scipost_file_doi']['filename'] = '/Users/jscaux/Sites/SciPost.org/scipost_v1/local_files/logs/doi.log'
CROSSREF_DEPOSIT_EMAIL = 'jscaux@scipost.org'

# Customized mailbackend
EMAIL_BACKEND = "mails.backends.filebased.ModelEmailBackend"
EMAIL_BACKEND_ORIGINAL = "mails.backends.filebased.EmailBackend"
