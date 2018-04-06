"""
WSGI config for SciPost_v1 project on Staging (jdewit.webfactional.com).
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciPost_v1.settings.staging")

application = get_wsgi_application()
