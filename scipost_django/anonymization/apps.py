__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.apps import AppConfig


class AnonymizationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "anonymization"
