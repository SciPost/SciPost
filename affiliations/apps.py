from django.apps import AppConfig
from django.db.models.signals import post_save


class AffiliationsConfig(AppConfig):
    name = 'affiliations'

    def ready(self):
        super().ready()

        from . import models, signals
        post_save.connect(signals.notify_new_affiliation,
                          sender=models.Institution)
