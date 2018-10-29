from .base import *

# This file is meant for the server used for the release branches
#

# THE MAIN THING HERE
DEBUG = False
ALLOWED_HOSTS = ['jdewit.webfactional.com']

# Recaptcha
RECAPTCHA_PUBLIC_KEY = get_secret("GOOGLE_RECAPTCHA_PUBLIC_KEY")
RECAPTCHA_PRIVATE_KEY = get_secret("GOOGLE_RECAPTCHA_PRIVATE_KEY")

# Static and media
STATIC_URL = '/static/'
STATIC_ROOT = '/home/jdewit/webapps/scipost_static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/jdewit/webapps/scipost_media/'

WEBPACK_LOADER['DEFAULT']['CACHE'] = True
WEBPACK_LOADER['DEFAULT']['BUNDLE_DIR_NAME'] = '/home/jdewit/webapps/scipost_static/bundles/'

# Logging
LOGGING['handlers']['scipost_file_arxiv']['filename'] = '/home/jdewit/webapps/scipost/logs/arxiv.log'
LOGGING['handlers']['scipost_file_doi']['filename'] = '/home/jdewit/webapps/scipost/logs/doi.log'

MONGO_DATABASE['user'] = get_secret('MONGO_DB_USER')
MONGO_DATABASE['password'] = get_secret('MONGO_DB_PASSWORD')
MONGO_DATABASE['port'] = get_secret("MONGO_DB_PORT")
