from .base import *

# THE MAIN THING HERE
DEBUG = True

# Debug toolbar settings
INSTALLED_APPS += (
    'debug_toolbar',
)
MIDDLEWARE_CLASSES += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)
INTERNAL_IPS = ['127.0.0.1', '::1']

# Static and media
STATIC_ROOT = '/Users/jorranwit/Develop/SciPost/scipost_v1/local_files/static/'
MEDIA_ROOT = '/Users/jorranwit/Develop/SciPost/scipost_v1/local_files/media/'
WEBPACK_LOADER['DEFAULT']['BUNDLE_DIR_NAME'] =\
    '/Users/jorranwit/Develop/SciPost/scipost_v1/local_files/static/bundles/'

MAILCHIMP_API_USER = get_secret("MAILCHIMP_API_USER")
MAILCHIMP_API_KEY = get_secret("MAILCHIMP_API_KEY")
