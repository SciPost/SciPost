# Used on staging server with IP https://scipoststg.webfactional.com

from .base import *

# THE MAIN THING HERE
DEBUG = False
ALLOWED_HOSTS = ["scipoststg.webfactional.com", "www.scipoststg.webfactional.com"]

# Static and media
STATIC_ROOT = "/home/scipoststg/webapps/scipost_static/"
MEDIA_ROOT = "/home/scipoststg/webapps/scipost_media/"

# Webpack
WEBPACK_LOADER["DEFAULT"]["CACHE"] = True
WEBPACK_LOADER["DEFAULT"][
    "BUNDLE_DIR_NAME"
] = "/home/scipoststg/webapps/scipost_static/bundles/"

# ReCaptcha keys
RECAPTCHA_PUBLIC_KEY = get_secret("GOOGLE_RECAPTCHA_PUBLIC_KEY")
RECAPTCHA_PRIVATE_KEY = get_secret("GOOGLE_RECAPTCHA_PRIVATE_KEY")

# Logging location
LOGGING["handlers"]["scipost_file_arxiv"][
    "filename"
] = "/home/scipoststg/webapps/scipost/logs/arxiv.log"
LOGGING["handlers"]["scipost_file_doi"][
    "filename"
] = "/home/scipoststg/webapps/scipost/logs/doi.log"

# Cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Email
EMAIL_BACKEND = "mails.backends.filebased.ModelEmailBackend"
EMAIL_BACKEND_ORIGINAL = (
    "django.core.mail.backends.dummy.EmailBackend"  # Disable real processing
)

# Mongo
MONGO_DATABASE["user"] = get_secret("MONGO_DB_USER")
MONGO_DATABASE["password"] = get_secret("MONGO_DB_PASSWORD")
MONGO_DATABASE["port"] = get_secret("MONGO_DB_PORT")
