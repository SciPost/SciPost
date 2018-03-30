# Used on staging server with IP https://scipoststg.webfactional.com

from .base import *

# THE MAIN THING HERE
DEBUG = True
ALLOWED_HOSTS = ['scipoststg.webfactional.com']

# Static and media
STATIC_ROOT = '/home/scipoststg/webapps/scipost_static/'
MEDIA_ROOT = '/home/scipoststg/webapps/scipost_media/'

# Webpack
WEBPACK_LOADER['DEFAULT']['CACHE'] = True
WEBPACK_LOADER['DEFAULT']['BUNDLE_DIR_NAME'] = '/home/scipoststg/webapps/scipost_static/bundles/'

# ReCaptcha keys
RECAPTCHA_PUBLIC_KEY = get_secret("GOOGLE_RECAPTCHA_PUBLIC_KEY")
RECAPTCHA_PRIVATE_KEY = get_secret("GOOGLE_RECAPTCHA_PRIVATE_KEY")

# Logging location
LOGGING['handlers']['scipost_file_arxiv']['filename'] = '/home/scipoststg/webapps/scipost/logs/arxiv.log'
LOGGING['handlers']['scipost_file_doi']['filename'] = '/home/scipoststg/webapps/scipost/logs/doi.log'
