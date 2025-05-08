__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from profiles.managers import ProfileQuerySet
from scipost.managers import ContributorQuerySet


class AnonymousProfileManager(models.Manager.from_queryset(ProfileQuerySet)):
    def get_queryset(self):
        return super().get_queryset().anonymous()


class AnonymousContributorManager(models.Manager.from_queryset(ContributorQuerySet)):
    def get_queryset(self):
        return super().get_queryset().anonymous()
