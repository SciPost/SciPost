__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.db import models
from django.db.models import QuerySet


class SeriesQuerySet(QuerySet):

    def of_single_journal(self):
        return self.annotate(
            nr_container_journals=models.Count("container_journals")
        ).filter(nr_container_journals=1)
