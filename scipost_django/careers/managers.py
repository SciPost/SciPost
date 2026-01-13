__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from datetime import datetime
from django.db.models import QuerySet, Q

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from careers.models import WorkContract


class JobOpeningQuerySet(QuerySet):
    def drafted(self):
        from careers.models import JobOpening

        return self.filter(status=JobOpening.DRAFTED)

    def publicly_visible(self):
        from careers.models import JobOpening

        return self.filter(status=JobOpening.VISIBLE)

    def closed(self):
        from careers.models import JobOpening

        return self.filter(status=JobOpening.CLOSED)


class WorkContractQuerySet(QuerySet["WorkContract"]):
    def active(self):
        today = datetime.now().date()
        return (
            self.all()
            .filter(start_date__lte=today)
            .filter(Q(end_date__gte=today) | Q(end_date__isnull=True))
        )
