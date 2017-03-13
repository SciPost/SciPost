from .base import *
import os

# THE MAIN THING HERE
DEBUG = True

# Static and media
STATIC_ROOT = os.path.join(BASE_DIR, 'local_files', 'static')
MEDIA_ROOT = os.path.join(BASE_DIR, 'local_files', 'media')
WEBPACK_LOADER['DEFAULT']['BUNDLE_DIR_NAME'] =\
    os.path.join(BASE_DIR, 'static', 'bundles')
