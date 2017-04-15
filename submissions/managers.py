from django.db import models
from django.db.models import Q

from .constants import SUBMISSION_STATUS_OUT_OF_POOL, SUBMISSION_STATUS_PUBLICLY_UNLISTED,\
                       SUBMISSION_STATUS_PUBLICLY_INVISIBLE


class SubmissionManager(models.Manager):
    def get_pool(self, user):
        return self.exclude(status__in=SUBMISSION_STATUS_OUT_OF_POOL)\
                .exclude(is_current=False)\
                .exclude(authors=user.contributor)\
                .exclude(Q(author_list__icontains=user.last_name),
                         ~Q(authors_false_claims=user.contributor))\
                .order_by('-submission_date')

    def public(self):
        return self.exclude(status__in=SUBMISSION_STATUS_PUBLICLY_UNLISTED)

    def public_overcomplete(self):
        """
        This query contains an overcomplete set of public submissions, i.e. also containing
        submissions with status "published" or "resubmitted".
        """
        return self.exclude(status__in=SUBMISSION_STATUS_PUBLICLY_INVISIBLE)


class EditorialAssignmentManager(models.Manager):
    def get_for_user_in_pool(self, user):
        return self.exclude(submission__authors=user.contributor)\
                .exclude(Q(submission__author_list__icontains=user.last_name),
                         ~Q(submission__authors_false_claims=user.contributor))


class EICRecommendationManager(models.Manager):
    def get_for_user_in_pool(self, user):
        """
        -- DEPRECATED --

        Return list of EICRecommendation which are filtered as these objects
        are not related to the Contributor, by checking last_name and author_list of
        the linked Submission.
        """
        return self.exclude(submission__authors=user.contributor)\
                   .exclude(Q(submission__author_list__icontains=user.last_name),
                            ~Q(submission__authors_false_claims=user.contributor))

    def filter_for_user(self, user, **kwargs):
        """
        Return list of EICRecommendation which are owned linked to an author owned Submission.
        """
        return self.filter(submission__authors=user.contributor).filter(**kwargs)
