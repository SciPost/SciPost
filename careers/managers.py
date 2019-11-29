__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class JobOpeningQuerySet(models.QuerySet):

    def drafted(self):
        from careers.models import JobOpening
        return self.filter(status=JobOpening.DRAFTED)

    def publicly_visible(self):
        from careers.models import JobOpening
        return self.filter(status=JobOpening.VISIBLE)

    def closed(self):
        from careers.models import JobOpening
        return self.filter(status=JobOpening.CLOSED)
