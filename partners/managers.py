from django.db import models

from .constants import MEMBERSHIP_SUBMITTED


class MembershipAgreementManager(models.Manager):
    def submitted(self):
        return self.filter(status=MEMBERSHIP_SUBMITTED)
