from .base import *

# This file is meant for the server used for the release branches
#

# THE MAIN THING HERE
DEBUG = False
ALLOWED_HOSTS = ['jdewit.webfactional.com']

# Static and media
STATIC_URL = '/static/'
STATIC_ROOT = '/home/jdewit/webapps/scipost_static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/jdewit/webapps/scipost_media/'

WEBPACK_LOADER['DEFAULT']['CACHE'] = True,
WEBPACK_LOADER['DEFAULT']['BUNDLE_DIR_NAME'] = '/home/jdewit/webapps/scipost_static/bundles/'

# Error reporting
ADMINS = MANAGERS = (('J. de Wit', 'jorrandewit@outlook.com'), )

# Cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
