__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property

from ethics.managers import CompetingInterestQuerySet
from preprints.servers.server import PreprintServer

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.db.models import BaseConstraint
    from django.db.models.manager import RelatedManager
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
            case "EICRecommendation":
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
            case "EICRecommendation":
                return "Editor in Charge"
            case _:
                return self.content_type.model_class().__name__.lower() + " author"

    def get_authors_could_be_plural(self) -> bool:
        """
        Returns True if the content this disclosure is for could have multiple authors.
        """
        match self.content_type.model_class().__name__:
            case "Submission" | "Publication":
                return True
            case _:
                return False


class CoauthoredWork(models.Model):
    """
    A work (e.g. preprint, publication, project, ...) that has multiple co-authors.
    Serves as a related document and "proof" for substantiating a Coauthorship.
    """

    server_source = models.CharField(max_length=64)
    work_type = models.CharField(max_length=64)
    identifier = models.CharField(max_length=256, null=True, blank=True)
    doi = models.CharField(max_length=256, null=True, blank=True)
    title = models.CharField(max_length=512)
    authors_str = models.TextField(
        help_text="Semicolon-separated list of authors with comma-separated name parts."
    )
    date_published = models.DateField(null=True, blank=True)
    date_updated = models.DateField(null=True, blank=True)
    date_fetched = models.DateField(auto_now_add=True)
    metadata = models.JSONField[str](default=dict, blank=True)

    if TYPE_CHECKING:
        coauthorships = RelatedManager["Coauthorship"]

    class Meta:
        constraints: list["BaseConstraint"] = [
            models.UniqueConstraint(
                fields=["server_source", "identifier"],
                name="unique_coauthored_work_id",
                nulls_distinct=True,
                violation_error_message="A coauthored work with this server and identifier already exists.",
            ),
        ]

    def __str__(self):
        work_type = f" {self.work_type}" if self.work_type else ""
        source_block = self.server_source + work_type
        return f"[{source_block}] {self.title} by {self.authors_str[:25]}"

    @cached_property
    def server(self):
        """Returns a PreprintServer if `server_source` corresponds to one."""
        try:
            return PreprintServer.from_name(self.server_source).server_class
        except ValueError:
            return None

    @property
    def url(self) -> str | None:
        if self.identifier and hasattr(self.server, "identifier_to_url"):
            return self.server.identifier_to_url(self.identifier)
        else:
            return self.doi_url

    @property
    def doi_url(self):
        if self.doi:
            return f"https://doi.org/{self.doi}"


class Coauthorship(models.Model):
    """
    An instance of a (potential) coauthorship between two Profiles. The profiles may
    share more than one coauthorship if it concerns a different work (publication).
    """

    STATUS_UNVERIFIED = "unverified"
    STATUS_VERIFIED = "verified"
    STATUS_DEPRECATED = "deprecated"
    COAUTHORSHIP_STATUSES = (
        (STATUS_UNVERIFIED, "Unverified"),
        (STATUS_VERIFIED, "Verified"),
        (STATUS_DEPRECATED, "Deprecated"),
    )

    profile = models.ForeignKey["Profile"](
        "profiles.Profile",
        on_delete=models.CASCADE,
        related_name="coauthorships",
    )
    coauthor = models.ForeignKey["Profile"](
        "profiles.Profile",
        on_delete=models.CASCADE,
        related_name="related_coauthorships",
    )
    work = models.ForeignKey[CoauthoredWork](
        "ethics.CoauthoredWork",
        on_delete=models.CASCADE,
        related_name="coauthorships",
    )
    status = models.CharField(
        max_length=16, choices=COAUTHORSHIP_STATUSES, default=STATUS_UNVERIFIED
    )
    verified_by = models.ForeignKey["Contributor"](
        "scipost.Contributor",
        on_delete=models.SET_NULL,
        null=True,
        related_name="coauthorships_verified",
    )

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        constraints: list["BaseConstraint"] = [
            models.UniqueConstraint(
                fields=["profile", "coauthor", "work"],
                name="unique_together_profile_coauthor_work",
                violation_error_message="This coauthorship already exists.",
            ),
            models.CheckConstraint(
                check=models.Q(profile_id__lt=models.F("coauthor_id")),
                name="enforce_profile_ordering",
                violation_error_message="Profile/Coauthor IDs must be in the correct order to avoid duplicates.",
            ),
        ]
        ordering = ["-created"]

    def verify(self, verified_by: "Contributor", commit: bool = True):
        self.status = Coauthorship.STATUS_VERIFIED
        self.verified_by = verified_by
        if commit:
            self.save()

    def deprecate(self, verified_by: "Contributor", commit: bool = True):
        self.status = Coauthorship.STATUS_DEPRECATED
        self.verified_by = verified_by
        if commit:
            self.save()

    def __str__(self):
        return f"Coauthorship: {self.profile} & {self.coauthor} [{self.get_status_display()}]"
