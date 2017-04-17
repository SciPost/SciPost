from django.db import models
from django.db.models import Q

from .constants import SUBMISSION_STATUS_OUT_OF_POOL, SUBMISSION_STATUS_PUBLICLY_UNLISTED,\
                       SUBMISSION_STATUS_PUBLICLY_INVISIBLE, STATUS_UNVETTED, STATUS_VETTED,\
                       STATUS_UNCLEAR, STATUS_INCORRECT, STATUS_NOT_USEFUL, STATUS_NOT_ACADEMIC,\
                       SUBMISSION_HTTP404_ON_EDITORIAL_PAGE


class SubmissionManager(models.Manager):
    def user_filter(self, user):
        """
        Prevent conflic of interest by filtering submissions possible related to user.
        This filter should be inherited by other filters.
        """
        return (self.exclude(authors=user.contributor)
                .exclude(Q(author_list__icontains=user.last_name),
                         ~Q(authors_false_claims=user.contributor)))

    def get_pool(self, user):
        """
        This filter will return submission currently in an active submission cycle.
        """
        return (self.user_filter(user)
                .exclude(is_current=False)
                .exclude(status__in=SUBMISSION_STATUS_OUT_OF_POOL)
                .order_by('-submission_date'))

    def filter_editorial_page(self, user):
        """
        This filter returns a subgroup of the `get_pool` filter, to allow opening and editing
        certain submissions that are officially out of the submission cycle i.e. due
        to resubmission, but should still have the possibility to be opened by the EIC.
        """
        return (self.user_filter(user)
                .exclude(status__in=SUBMISSION_HTTP404_ON_EDITORIAL_PAGE)
                .order_by('-submission_date'))

    def public(self):
        '''List only all public submissions. Should be used as a default filter!'''
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
        Return list of EICRecommendation's which are owned/assigned author through the
        related submission.
        """
        return self.filter(submission__authors=user.contributor).filter(**kwargs)


class ReportManager(models.Manager):
    def accepted(self):
        return self.filter(status__gte=STATUS_VETTED)

    def awaiting_vetting(self):
        return self.filter(status=STATUS_UNVETTED)

    def rejected(self):
        return self.filter(status__in=[STATUS_UNCLEAR, STATUS_INCORRECT,
                                       STATUS_NOT_USEFUL, STATUS_NOT_ACADEMIC])
