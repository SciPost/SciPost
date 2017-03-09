from .base import *

# THE MAIN THING HERE
DEBUG = True

# Static and media
STATIC_ROOT = '/Users/jorranwit/Develop/SciPost/scipost_v1/local_files/static/'
MEDIA_ROOT = '/Users/jorranwit/Develop/SciPost/scipost_v1/local_files/media/'
WEBPACK_LOADER['DEFAULT']['BUNDLE_DIR_NAME'] =\
    '/Users/jorranwit/Develop/SciPost/scipost_v1/local_files/static/bundles/'
