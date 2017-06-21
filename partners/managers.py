from django.db import models

from .constants import MEMBERSHIP_SUBMITTED, PROSPECTIVE_PARTNER_PROCESSED


class ProspectivePartnerManager(models.Manager):
    def not_yet_partner(self):
        return self.exclude(status=PROSPECTIVE_PARTNER_PROCESSED)


class MembershipAgreementManager(models.Manager):
    def submitted(self):
        return self.filter(status=MEMBERSHIP_SUBMITTED)
