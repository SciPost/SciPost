__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models

from . import constants


class ProductionUserQuerySet(models.QuerySet):
    def active(self):
        return self.filter(user__isnull=False)


class ProductionStreamQuerySet(models.QuerySet):
    def completed(self):
        return self.filter(status=constants.PRODUCTION_STREAM_COMPLETED)

    def ongoing(self):
        return self.exclude(status=constants.PRODUCTION_STREAM_COMPLETED)

    def filter_for_user(self, production_user):
        """
        Return ProductionStreams that are only assigned to me as a Production Officer
        or a Inivtations Officer.
        """
        return self.filter(
            models.Q(officer=production_user)
            | models.Q(invitations_officer=production_user)
        )


class ProductionEventManager(models.Manager):
    def get_my_events(self, production_user):
        return self.filter(noted_by=production_user)

    def all_without_duration(self):
        return self.filter(duration__isnull=True)


class ProofsQuerySet(models.QuerySet):
    def for_authors(self):
        return self.filter(accessible_for_authors=True)

    def can_be_send(self):
        return self.filter(
            status__in=[
                constants.PROOFS_UPLOADED,
                constants.PROOFS_SENT,
                constants.PROOFS_ACCEPTED_SUP,
            ]
        )
