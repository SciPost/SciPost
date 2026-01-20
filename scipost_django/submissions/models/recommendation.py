__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from typing import TYPE_CHECKING
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone

from ..behaviors import SubmissionRelatedObjectMixin
from ..constants import (
    EIC_REC_CHOICES,
    EIC_REC_CHOICES_SHORT,
    EIC_REC_MAJOR_REVISION,
    EIC_REC_MINOR_REVISION,
    EIC_REC_STATUSES,
    DECISION_FIXED,
    DEPRECATED,
    EIC_REC_STATUSES_SHORT,
    VOTING_IN_PREP,
    PUT_TO_VOTING,
    ALT_REC_CHOICES,
)
from ..managers import EICRecommendationQuerySet

if TYPE_CHECKING:
    from scipost.models import Contributor
    from submissions.models import Submission
    from journals.models import Journal


class EICRecommendation(SubmissionRelatedObjectMixin, models.Model):
    """
    A recommendation formulated by the EIC for a specific Submission.

    The EICRecommendation on a Submission is formulated by the Editor-in-charge
    at the end of the refereeing cycle. If it recommends a minor/major revision,
    it is communicated directly to the authors. If it recommends to publish or
    reject, it is voted on by chosen Fellows of the appropriate Editorial College.
    """

    submission = models.ForeignKey["Submission"](
        "submissions.Submission",
        on_delete=models.CASCADE,
        related_name="eicrecommendations",
    )
    formulated_by = models.ForeignKey["Contributor"](
        "scipost.Contributor",
        on_delete=models.SET_NULL,
        null=True,
        related_name="eic_recommendations_formulated",
    )

    date_submitted = models.DateTimeField("date submitted", default=timezone.now)
    remarks_for_authors = models.TextField(blank=True, null=True)
    requested_changes = models.TextField(
        verbose_name="requested changes", blank=True, null=True
    )
    remarks_for_editorial_college = models.TextField(
        blank=True, verbose_name="Remarks for the Editorial College"
    )
    for_journal = models.ForeignKey["Journal"](
        "journals.Journal", blank=True, null=True, on_delete=models.SET_NULL
    )
    recommendation = models.SmallIntegerField(choices=EIC_REC_CHOICES)
    status = models.CharField(
        max_length=32, choices=EIC_REC_STATUSES, default=VOTING_IN_PREP
    )
    version = models.SmallIntegerField(default=1)
    active = models.BooleanField(default=True)

    gen_ai_disclosures = GenericRelation(
        "ethics.GenAIDisclosure",
        content_type_field="content_type",
        object_id_field="object_id",
        related_query_name="eic_recommendation",
    )

    # Editorial Fellows who have assessed this recommendation:
    eligible_to_vote = models.ManyToManyField["EICRecommendation", "Contributor"](
        "scipost.Contributor", blank=True, related_name="eligible_to_vote"
    )
    voted_for = models.ManyToManyField["EICRecommendation", "Contributor"](
        "scipost.Contributor", blank=True, related_name="voted_for"
    )
    voted_against = models.ManyToManyField["EICRecommendation", "Contributor"](
        "scipost.Contributor", blank=True, related_name="voted_against"
    )
    voted_abstain = models.ManyToManyField["EICRecommendation", "Contributor"](
        "scipost.Contributor", blank=True, related_name="voted_abstain"
    )
    voting_deadline = models.DateTimeField("date submitted", default=timezone.now)

    objects = EICRecommendationQuerySet.as_manager()

    class Meta:
        unique_together = ("submission", "version")
        ordering = ["version"]

    def __str__(self):
        """Summarize the EICRecommendation's meta information."""
        return "{title} by {author}, {recommendation} version {version}".format(
            title=self.submission.title[:20],
            author=self.submission.author_list[:30],
            recommendation=self.get_recommendation_display(),
            version=self.version,
        )

    def get_absolute_url(self):
        """Return the url of the Submission detail page.

        Note that the EICRecommendation is not publicly visible, so the use of this url
        is limited.
        """
        return self.submission.get_absolute_url()

    @property
    def nr_for(self):
        """Return the number of votes 'for'."""
        return self.voted_for.count()

    @property
    def nr_against(self):
        """Return the number of votes 'against'."""
        return self.voted_against.count()

    @property
    def nr_abstained(self):
        """Return the number of votes 'abstained'."""
        return self.voted_abstain.count()

    @property
    def is_deprecated(self):
        """Check if Recommendation is deprecated."""
        return self.status == DEPRECATED

    @property
    def may_be_reformulated(self):
        """Check if this EICRecommdation is allowed to be reformulated in a new version."""
        if self.status == DEPRECATED:
            # Already reformulated before; please use the latest version
            return self.submission.eicrecommendations.last() == self
        return self.status != DECISION_FIXED

    @property
    def voting_in_preparation(self):
        return self.status == VOTING_IN_PREP

    @property
    def undergoing_voting(self):
        return self.status == PUT_TO_VOTING

    @property
    def decision_fixed(self):
        return self.status == DECISION_FIXED

    @property
    def contributors_voted(self):
        return (
            self.voted_for.all() | self.voted_against.all() | self.voted_abstain.all()
        )

    @property
    def requires_voting(self):
        """
        True if the recommendation requires voting by the Editorial College,
        i.e. if it is not a mere revision, but rather publication or rejection.
        """
        return self.recommendation not in [
            EIC_REC_MINOR_REVISION,
            EIC_REC_MAJOR_REVISION,
        ]

    def get_other_versions(self):
        """Return other versions of EICRecommendations for this Submission."""
        return self.submission.eicrecommendations.exclude(id=self.id)

    def get_full_status_display(self):
        """Return `recommendation` and `status` field display."""
        return "{} ({})".format(
            self.get_recommendation_display(),
            self.get_status_display(),
        )

    def get_full_status_short_display(self):
        """Return `recommendation` and `status` field display in short form."""
        eicrec_short = self.get_recommendation_short_display()
        journal_name = self.get_for_journal_short_display()
        status_short = self.get_status_short_display()
        return f"{eicrec_short} - {journal_name} ({status_short})"

    def get_status_short_display(self):
        """Return `status` field display in short form."""
        return dict(EIC_REC_STATUSES_SHORT).get(self.status)

    def get_recommendation_short_display(self):
        """Return `recommendation` field display in short form."""
        return dict(EIC_REC_CHOICES_SHORT).get(self.recommendation)

    def get_for_journal_display(self):
        """Return `for_journal` field display."""
        return (
            str(self.for_journal)
            if self.for_journal is not None
            else "Any/all journals"
        )

    def get_for_journal_short_display(self):
        """Return `for_journal` field short display."""
        return (
            str(self.for_journal.name_abbrev)
            if self.for_journal is not None
            else "Any/all"
        )


class AlternativeRecommendation(models.Model):
    """Alternative recommendation from voting Fellow who disagrees with EICRec."""

    eicrec = models.ForeignKey(
        "submissions.EICRecommendation", on_delete=models.CASCADE
    )
    fellow = models.ForeignKey("scipost.Contributor", on_delete=models.CASCADE)
    for_journal = models.ForeignKey("journals.Journal", on_delete=models.CASCADE)
    recommendation = models.SmallIntegerField(choices=ALT_REC_CHOICES)
