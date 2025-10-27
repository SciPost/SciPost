__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import re
from nameparser import HumanName

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from ethics.managers import CoauthorshipQuerySet, ConflictOfInterestQuerySet
from preprints.servers.server import PreprintServer
from preprints.servers.utils import (
    AUTHOR_FIRST_LAST_NAME_FORMAT,
    Person,
    format_person_name,
)

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
    Assertion that a Profile has no conflicts of interest with regards to a Submission.
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


class ConflictOfInterest(models.Model):
    """
    Conflict of Interest relating two Profiles, affecting Submissions and Publications.
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
        related_name="conflicts_of_interest",
    )
    related_profile = models.ForeignKey["Profile"](
        "profiles.Profile",
        on_delete=models.CASCADE,
        related_name="related_conflicts_of_interest",
    )

    declared_by = models.ForeignKey["Contributor"](
        "scipost.Contributor",
        on_delete=models.CASCADE,
        related_name="declared_conflicts_of_interest",
    )
    declared_on = models.DateTimeField(default=timezone.now)

    comments = models.TextField(blank=True)

    exempted_submissions = models.ManyToManyField["Submission", "ConflictOfInterest"](
        "submissions.Submission",
        blank=True,
        related_name="exempted_cois",
    )

    if TYPE_CHECKING:
        coauthorship: "Coauthorship | None"

    objects = ConflictOfInterestQuerySet.as_manager()

    def __str__(self):
        return f"{self.profile} - {self.related_profile} ({self.get_nature_display()})"

    @classmethod
    def from_coauthorship(cls, coauthorship: "Coauthorship", **kwargs: Any):
        """
        Create a ConflictOfInterest instance from a Coauthorship instance.
        """
        coi = cls(
            nature=cls.COAUTHOR,
            date_from=coauthorship.work.date_published or timezone.now().date(),
            profile=coauthorship.profile,
            related_profile=coauthorship.coauthor,
            declared_by=coauthorship.verified_by,
            **kwargs,
        )
        return coi


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

    @property
    def server(self):
        """Returns a PreprintServer if `server_source` corresponds to one."""
        try:
            return PreprintServer.from_name(self.server_source).server_class
        except ValueError:
            return None

    @server.setter
    def server(self, server: PreprintServer | None):
        self.server_source = server.value if server else ""

    @property
    def authors(self) -> list[HumanName]:
        return [
            HumanName(author_name.strip())
            for author_name in self.authors_str.split(";")
        ]

    @authors.setter
    def authors(self, authors: list[HumanName]):
        self.authors_str = "; ".join(format_person_name(author) for author in authors)

    def map_people_to_author_idxs(self, *people: Person) -> dict[Person, int]:
        from common.utils.text import latinise, partial_name_match_regexp

        author_names = [
            format_person_name(author, format=AUTHOR_FIRST_LAST_NAME_FORMAT)
            for author in self.authors
        ]
        to_match_names = {
            person: format_person_name(person, format=AUTHOR_FIRST_LAST_NAME_FORMAT)
            for person in people
        }

        people_mapping: dict[Person, int] = {}
        for person, match_name in to_match_names.items():
            match_regex = partial_name_match_regexp(latinise(match_name.lower()))
            pattern = re.compile(match_regex)
            for i, author_name in enumerate(author_names):
                if i in people_mapping.values():
                    continue
                if pattern.match(latinise(author_name.lower())):
                    people_mapping[person] = i
                    break

        return people_mapping

    def contains_authors(self, *people: Person) -> bool:
        """
        Return True if all `people` are listed as authors of this work.
        Matching is done via `partial_name_match_regexp`, matching
        a 2+ sequence of name parts or initials thereof in any order,
        ignoring case and accents.
        """
        return len(people) == len(self.map_people_to_author_idxs(*people))

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
    conflict_of_interest = models.OneToOneField["ConflictOfInterest"](
        "ethics.ConflictOfInterest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coauthorship",
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
    _cf_profile_idx_in_authors_str = models.IntegerField(null=True, blank=True)
    _cf_coauthor_idx_in_authors_str = models.IntegerField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    objects = CoauthorshipQuerySet.as_manager()

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
        ordering = ["-status", "-work__date_published", "work__title"]

    @property
    def profile_idx_in_authors_str(self):
        if self._cf_profile_idx_in_authors_str is None:
            idx_map = self.work.map_people_to_author_idxs(self.profile)
            self._cf_profile_idx_in_authors_str = idx_map.get(self.profile, -1)
            self.save(update_fields=["_cf_profile_idx_in_authors_str"])
        return self._cf_profile_idx_in_authors_str

    @property
    def coauthor_idx_in_authors_str(self):
        if self._cf_coauthor_idx_in_authors_str is None:
            idx_map = self.work.map_people_to_author_idxs(self.coauthor)
            self._cf_coauthor_idx_in_authors_str = idx_map.get(self.coauthor, -1)
            self.save(update_fields=["_cf_coauthor_idx_in_authors_str"])
        return self._cf_coauthor_idx_in_authors_str

    @property
    def authors_contained(self):
        return self.work.contains_authors(self.profile, self.coauthor)

    def resolve_inconsistencies(self, commit: bool = True):
        """
        Re-order profile and coauthor to ensure profile_id < coauthor_id.
        Ensure that there are no profile-coauthor-work duplicates.
        """
        if self.profile_id > self.coauthor_id:
            self.profile_id, self.coauthor_id = self.coauthor_id, self.profile_id

        if duplicate := Coauthorship.objects.duplicate_of(self):
            self, to_delete = sorted((duplicate, self), key=lambda x: x.created)

            if to_delete.status == Coauthorship.STATUS_VERIFIED:
                self.status = Coauthorship.STATUS_VERIFIED
                self.verified_by = to_delete.verified_by
                self.conflict_of_interest = to_delete.conflict_of_interest

            to_delete.delete()

        if self and commit:
            self.save()

        return self

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

    def reset_status(self, commit: bool = True):
        self.status = Coauthorship.STATUS_UNVERIFIED
        self.verified_by = None
        if commit:
            self.save()

    def __str__(self):
        return f"Coauthorship: {self.profile} & {self.coauthor} [{self.get_status_display()}]"
