from django.db import models
from django.db.models import Q

from .constants import SUBMISSION_STATUS_OUT_OF_POOL


class SubmissionManager(models.Manager):
    def get_pool(self, user):
        return self.exclude(status__in=SUBMISSION_STATUS_OUT_OF_POOL)\
                .exclude(is_current=False)\
                .exclude(authors=user.contributor)\
                .exclude(Q(author_list__icontains=user.last_name),
                         ~Q(authors_false_claims=user.contributor))\
                .order_by('-submission_date')


class EditorialAssignmentManager(models.Manager):
    def get_for_user_in_pool(self, user):
        return self.exclude(submission__authors=user.contributor)\
                .exclude(Q(submission__author_list__icontains=user.last_name),
                         ~Q(submission__authors_false_claims=user.contributor))


class EICRecommendationManager(models.Manager):
    def get_for_user_in_pool(self, user):
        return self.exclude(submission__authors=user.contributor)\
                .exclude(Q(submission__author_list__icontains=user.last_name),
                         ~Q(submission__authors_false_claims=user.contributor))
