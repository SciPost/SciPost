__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.apps import AppConfig
from django.db.models.signals import post_save


class SciPostConfig(AppConfig):
    name = "scipost"

    def ready(self):
        super().ready()

        from . import signals
        from profiles.models import Profile

        post_save.connect(signals.link_created_profile_to_contributor, sender=Profile)
