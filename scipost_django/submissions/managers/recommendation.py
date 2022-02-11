__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db import models
from django.utils import timezone

from .. import constants


class EICRecommendationQuerySet(models.QuerySet):
    """QuerySet for the EICRecommendation model."""

    def user_must_vote_on(self, user):
        """Return the subset of EICRecommendation the User is requested to vote on."""
        if not hasattr(user, "contributor"):
            return self.none()

        return (
            self.put_to_voting()
            .filter(eligible_to_vote=user.contributor)
            .exclude(recommendation__in=[-1, -2])
            .exclude(
                models.Q(voted_for=user.contributor)
                | models.Q(voted_against=user.contributor)
                | models.Q(voted_abstain=user.contributor)
            )
            .exclude(
                submission__status__in=[
                    constants.STATUS_REJECTED,
                    constants.STATUS_PUBLISHED,
                    constants.STATUS_WITHDRAWN,
                ]
            )
            .distinct()
        )

    def user_current_voted(self, user):
        """
        Return the subset of EICRecommendations currently undergoing voting, for
        which the User has already voted.
        """
        if not hasattr(user, "contributor"):
            return self.none()
        return (
            self.put_to_voting()
            .filter(eligible_to_vote=user.contributor)
            .exclude(recommendation__in=[-1, -2])
            .filter(
                models.Q(voted_for=user.contributor)
                | models.Q(voted_against=user.contributor)
                | models.Q(voted_abstain=user.contributor)
            )
            .exclude(
                submission__status__in=[
                    constants.STATUS_REJECTED,
                    constants.STATUS_PUBLISHED,
                    constants.STATUS_WITHDRAWN,
                ]
            )
            .distinct()
        )

    def put_to_voting(self, longer_than_days=None):
        """Return the subset of EICRecommendation currently undergoing voting."""
        qs = self.filter(status=constants.PUT_TO_VOTING)
        if longer_than_days:
            qs = qs.filter(
                date_submitted__lt=timezone.now()
                - datetime.timedelta(days=longer_than_days)
            )
        return qs

    def voting_in_preparation(self):
        """Return the subset of EICRecommendation currently undergoing preparation for voting."""
        return self.filter(status=constants.VOTING_IN_PREP)

    def active(self):
        """Return the subset of non-deprecated EICRecommendations."""
        return self.exclude(status=constants.DEPRECATED)

    def fixed(self):
        """Return the subset of fixed EICRecommendations."""
        return self.filter(status=constants.DECISION_FIXED)

    def asking_revision(self):
        """Return EICRecommendation asking for a minor or major revision."""
        return self.filter(
            recommendation__in=[
                constants.EIC_REC_MINOR_REVISION,
                constants.EIC_REC_MAJOR_REVISION,
            ]
        )
