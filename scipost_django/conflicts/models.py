__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models

from .managers import ConflictOfInterestQuerySet


class ConflictOfInterest(models.Model):
    """
    A flagged relation between two scientists that could be conflicting in a refereeing
    phase.
    """

    STATUS_UNVERIFIED, STATUS_VERIFIED = "unverified", "verified"
    STATUS_DEPRECATED = "deprecated"
    CONFLICT_OF_INTEREST_STATUSES = (
        (STATUS_UNVERIFIED, "Unverified"),
        (STATUS_VERIFIED, "Verified by Admin"),
        (STATUS_DEPRECATED, "Deprecated"),
    )

    TYPE_OTHER, TYPE_COAUTHOR, TYPE_COWORKER = "other", "coauthor", "coworker"
    COI_TYPES = (
        (TYPE_COWORKER, "Co-worker"),
        (TYPE_COAUTHOR, "Co-authorship"),
        (TYPE_OTHER, "Other"),
    )

    status = models.CharField(
        max_length=16, choices=CONFLICT_OF_INTEREST_STATUSES, default=STATUS_UNVERIFIED
    )
    type = models.CharField(max_length=16, choices=COI_TYPES, default=TYPE_OTHER)
    profile = models.ForeignKey(
        "profiles.Profile", on_delete=models.CASCADE, related_name="conflicts"
    )
    related_profile = models.ForeignKey(
        "profiles.Profile", on_delete=models.CASCADE, related_name="related_conflicts"
    )

    # To
    related_submissions = models.ManyToManyField(
        "submissions.Submission", blank=True, related_name="conflict_of_interests"
    )

    header = models.CharField(max_length=265)
    url = models.URLField(blank=True)
    comment = models.TextField(blank=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    objects = ConflictOfInterestQuerySet.as_manager()

    def __str__(self):
        return "{} - {} ({})".format(
            self.profile, self.related_profile, self.get_type_display()
        )
