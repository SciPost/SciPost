from django.db import models

from .constants import PRODUCTION_STREAM_COMPLETED


class ProductionStreamQuerySet(models.QuerySet):
    def completed(self):
        return self.filter(status=PRODUCTION_STREAM_COMPLETED)

    def ongoing(self):
        return self.exclude(status=PRODUCTION_STREAM_COMPLETED)

    def filter_for_user(self, production_user):
        return self.filter(officer=production_user)


class ProductionEventManager(models.Manager):
    def get_my_events(self, production_user):
        return self.filter(noted_by=production_user)
