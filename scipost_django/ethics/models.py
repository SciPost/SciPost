__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from ethics.managers import CompetingInterestQuerySet

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scipost.models import Contributor
    from profiles.models import Profile
    from submissions.models import Submission
    from journals.models import Publication


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

    profile = models.ForeignKey["Profile"](
        "profiles.Profile",
        on_delete=models.CASCADE,
        related_name="competing_interests",
    )
    related_profile = models.ForeignKey["Profile"](
        "profiles.Profile",
        on_delete=models.CASCADE,
        related_name="related_competing_interests",
    )

    declared_by = models.ForeignKey["Contributor"](
        "scipost.Contributor",
        on_delete=models.CASCADE,
        related_name="declared_competing_interests",
    )
    declared_on = models.DateTimeField(default=timezone.now)

    affected_submissions = models.ManyToManyField["Submission", "CompetingInterest"](
        "submissions.Submission",
        blank=True,
        related_name="competing_interests",
    )

    affected_publications = models.ManyToManyField["Publication", "CompetingInterest"](
        "journals.Publication",
        blank=True,
        related_name="competing_interests",
    )

    comments = models.TextField(blank=True)

    objects = CompetingInterestQuerySet.as_manager()

    def __str__(self):
        return f"{self.profile} - {self.related_profile} ({self.get_nature_display()})"


class RedFlag(models.Model):
    concerning_object_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    concerning_object_id = models.PositiveIntegerField()
    concerning_object = GenericForeignKey(
        "concerning_object_type", "concerning_object_id"
    )

    description = models.TextField(blank=True)

    raised_by = models.ForeignKey["Contributor"](
        "scipost.Contributor",
        on_delete=models.CASCADE,
        related_name="red_flags_raised",
    )
    raised_on = models.DateField(default=timezone.now)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Red flag for {self.concerning_object} raised by {self.raised_by.profile} on {self.raised_on}"


class GenAIDisclosure(models.Model):
    """
    Generative AI use disclosure for contributor-generated content,
    such as submissions, publications, reports, comments, etc.
    """

    was_used = models.BooleanField(default=None, null=True, blank=True)
    use_details = models.TextField(blank=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    for_object = GenericForeignKey("content_type", "object_id")

    contributor = models.ForeignKey["Contributor"](
        "scipost.Contributor",
        on_delete=models.CASCADE,
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        default_related_name = "gen_ai_disclosures"
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id"],
                name="unique_gen_ai_disclosure_per_object",
                violation_error_message="GenAI disclosure already exists for this object.",
            ),
        ]

    def __str__(self):
        content_text = f"GenAI Disclosure for {self.for_object} by {self.contributor.profile} on {self.created}"
        match self.was_used:
            case True:
                return "Positive " + content_text
            case False:
                return "Negative " + content_text
            case None:
                return "Pending " + content_text

    def get_object_model_name(self):
        """
        Returns the model name of the object this disclosure is for.
        """
        match self.content_type.model_class().__name__:
            case "Submission":
                return "submission"
            case "Publication":
                return "publication"
            case "Comment":
                return "comment"
            case "Report":
                return "report"
            case "EIC Recommendation":
                return "recommendation"
            case _:
                return self.content_type.model_class().__name__.lower()

    def get_content_author_name(self):
        """
        Returns the semantic name of the author who created the content this disclosure is for.
        """
        match self.content_type.model_class().__name__:
            case "Submission" | "Publication":
                return "author(s)"
            case "Comment":
                return "comment author"
            case "Report":
                return "referee"
            case "EIC Recommendation":
                return "editor-in-charge"
            case _:
                return self.content_type.model_class().__name__.lower() + " author"
