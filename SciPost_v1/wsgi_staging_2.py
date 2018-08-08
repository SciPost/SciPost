"""
WSGI config for SciPost_v1 project on Production (ip: 87.247.240.135).
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciPost_v1.settings.staging_2")

application = get_wsgi_application()
