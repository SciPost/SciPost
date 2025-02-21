from SciPost_v1.settings.base import *
import re
import os


def env_or_secret(name, env_prefix="SP_"):
    return os.environ.get(env_prefix + name, get_secret(name))


# THE MAIN THING HERE
DEBUG = os.environ.get("SP_DEBUG", "False") == "True"

# Enable django-debug-toolbar
if DEBUG:
    INSTALLED_APPS += [
        "debug_toolbar",
    ]
    MIDDLEWARE = MIDDLEWARE + [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ]
    DEBUG_TOOLBAR_CONFIG = {
        "RESULTS_CACHE_SIZE": 300,
        "SHOW_COLLAPSED": True,
    }

if "maintenancemode" in INSTALLED_APPS:
    INSTALLED_APPS.remove("maintenancemode")

if "maintenancemode.middleware.MaintenanceModeMiddleware" in MIDDLEWARE:
    MIDDLEWARE.remove("maintenancemode.middleware.MaintenanceModeMiddleware")


# Static and media
LOCAL_DATA_PATH = "/data/scipost"
MEDIA_ROOT = LOCAL_DATA_PATH + "/media/"
MEDIA_ROOT_SECURE = LOCAL_DATA_PATH + "/secure_media/"
STATIC_ROOT = LOCAL_DATA_PATH + "/static/"
WEBPACK_LOADER["DEFAULT"]["BUNDLE_DIR_NAME"] = STATIC_ROOT + "bundles/"

# CROSSREF_LOGIN_ID = get_secret("CROSSREF_LOGIN_ID")
# CROSSREF_LOGIN_PASSWORD = get_secret("CROSSREF_LOGIN_PASSWORD")
CROSSREF_DEBUG = True

ITHENTICATE_USERNAME = env_or_secret("ITHENTICATE_USERNAME")
ITHENTICATE_PASSWORD = env_or_secret("ITHENTICATE_PASSWORD")

# MAILCHIMP_API_USER = get_secret("MAILCHIMP_API_USER")
# MAILCHIMP_API_KEY = get_secret("MAILCHIMP_API_KEY")

LOG_PATH = "/var/log/scipost/"
for handler_name, handler_config in LOGGING["handlers"].items():
    if "filename" in handler_config:
        handler_config["filename"] = handler_config["filename"].replace(
            "path/to/logs/", LOG_PATH
        )

# Customized mailbackend
EMAIL_BACKEND = "mails.backends.filebased.ModelEmailBackend"
EMAIL_FILE_PATH = LOCAL_DATA_PATH + "/mail_output"
EMAIL_BACKEND_ORIGINAL = "mails.backends.filebased.EmailBackend"


# # CSP
# CSP_REPORT_URI = get_secret('CSP_SENTRY')
# CSP_REPORT_ONLY = True

# # Mailgun credentials
# MAILGUN_API_KEY = get_secret('MAILGUN_API_KEY')

# CORS headers
CORS_ALLOW_ALL_ORIGINS = True  # Dev only!

# GitLab API
GITLAB_ROOT = "SciPost"
GITLAB_URL = "git.scipost.org"
GITLAB_KEY = env_or_secret("GITLAB_KEY")


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env_or_secret("DB_NAME"),
        "USER": env_or_secret("DB_USER"),
        "PASSWORD": env_or_secret("DB_PWD"),
        "HOST": "scipost-postgres",
        "PORT": "5432",
    }
}
