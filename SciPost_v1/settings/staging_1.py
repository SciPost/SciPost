# Used on staging server with IP http://146.185.181.185/
# A Digital Ocean setup

from .base import *

# THE MAIN THING HERE
DEBUG = True
ALLOWED_HOSTS = ['146.185.181.185']

# Static and media
STATIC_ROOT = '/home/django/scipost_v1/static/'
MEDIA_ROOT = '/home/django/scipost_v1/media/'
WEBPACK_LOADER['DEFAULT']['BUNDLE_DIR_NAME'] = '/home/django/scipost_v1/static/bundles/'

JOURNALS_DIR = 'journals_dir'
