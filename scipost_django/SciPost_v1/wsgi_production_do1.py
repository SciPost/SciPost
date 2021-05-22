__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


"""
WSGI config for SciPost_v1 project on Production (on Digital Ocean from 2020-11, IP 142.93.224.252).
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciPost_v1.settings.production_do1")

application = get_wsgi_application()
