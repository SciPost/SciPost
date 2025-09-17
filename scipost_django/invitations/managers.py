__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models

from . import constants


class RegistrationInvitationQuerySet(models.QuerySet):
    def for_contributors(self):
        return self.filter(invitation_type=constants.INVITATION_CONTRIBUTOR)

    def for_fellows(self):
        return self.filter(invitation_type=constants.INVITATION_EDITORIAL_FELLOW)

    def not_for_fellows(self):
        return self.exclude(invitation_type=constants.INVITATION_EDITORIAL_FELLOW)

    def declined(self):
        return self.filter(status=constants.STATUS_DECLINED)

    def drafts(self):
        return self.filter(status=constants.STATUS_DRAFT)

    def declined_or_without_response(self):
        return self.filter(
            status__in=[
                constants.STATUS_DECLINED,
                constants.STATUS_SENT,
                constants.STATUS_DRAFT,
                constants.STATUS_SENT_AND_EDITED,
            ]
        )

    def not_expired(self):
        return self.filter(key_expires__gt=models.functions.Now())

    def sent(self):
        return self.filter(
            status__in=[constants.STATUS_SENT, constants.STATUS_SENT_AND_EDITED]
        )

    def no_response(self):
        return self.filter(
            status__in=[
                constants.STATUS_SENT,
                constants.STATUS_DRAFT,
                constants.STATUS_SENT_AND_EDITED,
            ]
        )

    def invited_by(self, user):
        return self.filter(invited_by=user)

    def created_by(self, user):
        return self.filter(created_by=user)


class CitationNotificationQuerySet(models.QuerySet):
    def for_submissions(self):
        return self.filter(submission__isnull=False)

    def for_publications(self):
        return self.filter(publication__isnull=False)

    def unprocessed(self):
        return self.filter(processed=False)

    def processed(self):
        return self.filter(processed=False)
