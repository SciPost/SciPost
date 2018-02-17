from django.db import models

from . import constants


class RegistrationInvitationQuerySet(models.QuerySet):
    def for_fellows(self):
        return self.filter(invitation_type=constants.INVITATION_EDITORIAL_FELLOW)

    def not_for_fellows(self):
        return self.exclude(invitation_type=constants.INVITATION_EDITORIAL_FELLOW)

    def declined(self):
        return self.filter(status=constants.STATUS_DECLINED)

    def drafts(self):
        return self.filter(status=constants.STATUS_DRAFT)

    def pending_response(self):
        return self.filter(status=constants.STATUS_SENT)

    def invited_by(self, user):
        return self.filter(invited_by=user)
