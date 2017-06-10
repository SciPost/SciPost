from django.db import models

from .constants import PRODUCTION_STREAM_COMPLETED, PRODUCTION_STREAM_ONGOING


class ProductionStreamManager(models.Manager):
    def completed(self):
        return self.filter(status=PRODUCTION_STREAM_COMPLETED)

    def ongoing(self):
        return self.filter(status=PRODUCTION_STREAM_ONGOING)


class ProductionEventManager(models.Manager):
    def get_my_events(self, current_contributor):
        return self.filter(noted_by=current_contributor)
