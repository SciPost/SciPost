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

    def sent(self):
        return self.filter(status__in=[constants.STATUS_SENT, constants.STATUS_SENT_AND_EDITED])

    def no_response(self):
        return self.filter(status__in=[constants.STATUS_SENT,
                                       constants.STATUS_DRAFT,
                                       constants.STATUS_SENT_AND_EDITED])

    def invited_by(self, user):
        return self.filter(invited_by=user)


class CitationNotificationQuerySet(models.QuerySet):
    def for_submissions(self):
        return self.filter(submission__isnull=False)

    def for_publications(self):
        return self.filter(publication__isnull=False)

    def unprocessed(self):
        return self.filter(processed=False)

    def processed(self):
        return self.filter(processed=False)
