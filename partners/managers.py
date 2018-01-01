from django.db import models
from django.utils import timezone

from .constants import MEMBERSHIP_SUBMITTED, PROSPECTIVE_PARTNER_PROCESSED, REQUEST_INITIATED


class ContactRequestManager(models.Manager):
    def awaiting_processing(self):
        return self.filter(status=REQUEST_INITIATED)


class ProspectivePartnerManager(models.Manager):
    def not_yet_partner(self):
        return self.exclude(status=PROSPECTIVE_PARTNER_PROCESSED)


class PartnerManager(models.Manager):
    def my_partners(self, current_user):
        """
        Filter out my Partners if user is not a PartnerAdmin.
        """
        if current_user.has_perm('scipost.can_view_partners'):
            return self.all()
        return self.filter(contact=current_user.partner_contact)


class MembershipAgreementManager(models.Manager):
    def submitted(self):
        return self.filter(status=MEMBERSHIP_SUBMITTED)

    def open_to_partner(self):
        return self.exclude(status=MEMBERSHIP_SUBMITTED)

    def now_active(self):
        return self.filter(start_date__lte=timezone.now().date(),
                           end_date__gte=timezone.now().date())


class PartnersAttachmentManager(models.Manager):
    def my_attachments(self, current_user):
        if current_user.has_perm('scipost.can_view_partners'):
            return self.all()
