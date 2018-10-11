__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db import models


class OrganizationQuerySet(models.QuerySet):

    def current_sponsors(self):
        return self.filter(subsidy__date_until__gte=datetime.date.today())
