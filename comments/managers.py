from django.db import models

from .constants import STATUS_PENDING


class CommentQuerySet(models.QuerySet):
    def vetted(self):
        return self.filter(status__gte=1)

    def awaiting_vetting(self):
        return self.filter(status=STATUS_PENDING)
