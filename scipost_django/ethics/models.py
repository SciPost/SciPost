__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.utils import timezone

from ethics.managers import CompetingInterestQuerySet


class SubmissionClearance(models.Model):
    """
    Assertion that a Profile has no competing interests with regards to a Submission.
    """

    profile = models.ForeignKey(
        "profiles.Profile",
        on_delete=models.CASCADE,
        related_name="submission_clearances",
    )

    submission = models.ForeignKey(
        "submissions.Submission",
        on_delete=models.CASCADE,
        related_name="clearances",
    )

    asserted_by = models.ForeignKey(
        "scipost.Contributor",
        on_delete=models.CASCADE,
        related_name="asserted_submission_clearances",
    )
    asserted_on = models.DateTimeField(default=timezone.now)

    comments = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "submission"],
                name="unique_together_profile_submission",
            ),
        ]
        ordering = ["submission", "profile"]

    def __str__(self):
        return f"{self.profile} clearance for {self.submission}"


class CompetingInterest(models.Model):
    """
    Competing interest relating two Profiles, affecting Submissions and Publications.
    """

    COAUTHOR = "coauthor"
    COLLEAGUE = "colleague"
    PhD_SUPERVISOR = "PhD_supervisor"
    PhD_SUPERVISEE = "PhD_supervisee"
    POSTDOC_SUPERVISOR = "postdoc_supervisor"
    POSTDOC_SUPERVISEE = "postdoc_supervisee"
    COMPETITOR = "competitor"
    DISACCORD = "disaccord"
    SHARED_FUNDING = "shared_funding"
    PERSONAL_RELATIONSHIP = "personal"
    FAMILY = "family"
    FINANCIAL = "financial"
    OTHER = "other"
    NATURE_CHOICES = (
        (COAUTHOR, "Coauthor"),
        (COLLEAGUE, "Colleague"),
        (PhD_SUPERVISOR, "PhD supervisor"),
        (PhD_SUPERVISEE, "PhD supervisee"),
        (POSTDOC_SUPERVISOR, "Postdoc supervisor"),
        (POSTDOC_SUPERVISEE, "Postdoc supervisee"),
        (COMPETITOR, "Competitor"),
        (DISACCORD, "Professional disaccord"),
        (SHARED_FUNDING, "Involved in shared funding"),
        (PERSONAL_RELATIONSHIP, "Involved in a personal relationship"),
        (FAMILY, "Family ties"),
        (FINANCIAL, "Financial ties"),
        (OTHER, "Other"),
    )

    nature = models.CharField(max_length=32, choices=NATURE_CHOICES)

    date_from = models.DateField(blank=True, null=True)
    date_until = models.DateField(blank=True, null=True)

    profile = models.ForeignKey(
        "profiles.Profile",
        on_delete=models.CASCADE,
        related_name="competing_interests",
    )
    related_profile = models.ForeignKey(
        "profiles.Profile",
        on_delete=models.CASCADE,
        related_name="related_competing_interests",
    )

    declared_by = models.ForeignKey(
        "scipost.Contributor",
        on_delete=models.CASCADE,
        related_name="declared_competing_interests",
    )
    declared_on = models.DateTimeField(default=timezone.now)

    affected_submissions = models.ManyToManyField(
        "submissions.Submission",
        blank=True,
        related_name="competing_interests",
    )

    affected_publications = models.ManyToManyField(
        "journals.Publication",
        blank=True,
        related_name="competing_interests",
    )

    comments = models.TextField(blank=True)

    objects = CompetingInterestQuerySet.as_manager()

    def __str__(self):
        return f"{self.profile} - {self.related_profile} ({self.get_nature_display()})"
