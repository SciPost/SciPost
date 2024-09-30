__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
from typing import TYPE_CHECKING
import feedparser
import uuid

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property

from guardian.models import UserObjectPermissionBase, GroupObjectPermissionBase
from guardian.shortcuts import assign_perm, remove_perm

from scipost.behaviors import TimeStampedModel
from scipost.constants import SCIPOST_APPROACHES
from scipost.fields import ChoiceArrayField
from scipost.models import Contributor

from comments.models import Comment
from colleges.models.fellowship import Fellowship
from submissions.models.assignment import EditorialAssignment

from ..behaviors import SubmissionRelatedObjectMixin
from ..constants import (
    CYCLE_UNDETERMINED,
    SUBMISSION_CYCLES,
    CYCLE_DEFAULT,
    CYCLE_SHORT,
    CYCLE_DIRECT_REC,
    EVENT_TYPES,
    EVENT_GENERAL,
    EVENT_FOR_EDADMIN,
    EVENT_FOR_AUTHOR,
    EVENT_FOR_EIC,
    SUBMISSION_TIERS,
    STATUS_VETTED,
)
from ..exceptions import StageNotDefinedError
from ..managers import SubmissionQuerySet, SubmissionEventQuerySet
from ..refereeing_cycles import ShortCycle, DirectCycle, RegularCycle

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager
    from submissions.models import EditorialDecision, RefereeInvitation, Report
    from submissions.models.assignment import ConditionalAssignmentOffer
    from scipost.models import Contributor
    from journals.models import Journal, Publication
    from proceedings.models import Proceedings
    from iThenticate_report import iThenticateReport
    from ontology.models import AcademicField, Specialty, Topic
    from series.models import Collection


class SubmissionAuthorProfile(models.Model):
    submission = models.ForeignKey(
        "submissions.Submission",
        on_delete=models.CASCADE,
        related_name="author_profiles",
    )
    profile = models.ForeignKey(
        "profiles.Profile",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    affiliations = models.ManyToManyField("organizations.Organization", blank=True)
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = (
            "submission",
            "order",
        )

    def __str__(self):
        return str(self.profile)

    def save(self, *args, **kwargs):
        """Auto increment order number if not explicitly set."""
        if not self.order:
            self.order = self.submission.author_profiles.count() + 1
        return super().save(*args, **kwargs)

    @property
    def is_registered(self):
        """Check if author is registered at SciPost."""
        return self.profile.contributor is not None

    @property
    def first_name(self):
        """Return first name of author."""
        return self.profile.first_name

    @property
    def last_name(self):
        """Return last name of author."""
        return self.profile.last_name


class Submission(models.Model):
    """
    A Submission is a preprint sent to SciPost for consideration.
    """

    # Possible statuses
    INCOMING = "incoming"
    ADMISSIBLE = "admissible"
    ADMISSION_FAILED = "admission_failed"
    PREASSIGNMENT = "preassignment"
    PREASSIGNMENT_FAILED = "preassignment_failed"
    SEEKING_ASSIGNMENT = "seeking_assignment"
    ASSIGNMENT_FAILED = "assignment_failed"
    REFEREEING_IN_PREPARATION = "refereeing_in_preparation"
    IN_REFEREEING = "in_refereeing"
    REFEREEING_CLOSED = "refereeing_closed"
    AWAITING_RESUBMISSION = "awaiting_resubmission"
    RESUBMITTED = "resubmitted"
    VOTING_IN_PREPARATION = "voting_in_preparation"
    IN_VOTING = "in_voting"
    AWAITING_DECISION = "awaiting_decision"
    ACCEPTED_IN_TARGET = "accepted_in_target"
    ACCEPTED_IN_ALTERNATIVE_AWAITING_PUBOFFER_ACCEPTANCE = (
        "accepted_alt_puboffer_waiting"
    )
    ACCEPTED_IN_ALTERNATIVE = "accepted_alt"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    PUBLISHED = "published"

    SUBMISSION_STATUSES = (
        (INCOMING, "Submission incoming, awaiting EdAdmin"),
        (ADMISSIBLE, "Admissible, undergoing further admission checks"),
        (ADMISSION_FAILED, "Admission failed"),
        (PREASSIGNMENT, "In preassignment"),
        (PREASSIGNMENT_FAILED, "Preassignment failed"),
        (SEEKING_ASSIGNMENT, "Seeking assignment"),
        (
            ASSIGNMENT_FAILED,
            "Failed to assign Editor-in-charge; manuscript rejected",
        ),
        (REFEREEING_IN_PREPARATION, "Refereeing in preparation"),
        (IN_REFEREEING, "In refereeing"),
        (REFEREEING_CLOSED, "Refereeing closed (awaiting author replies and EdRec)"),
        (AWAITING_RESUBMISSION, "Awaiting resubmission"),
        (RESUBMITTED, "Has been resubmitted"),
        (VOTING_IN_PREPARATION, "Voting in preparation"),
        (IN_VOTING, "In voting"),
        (AWAITING_DECISION, "Awaiting decision"),
        (ACCEPTED_IN_TARGET, "Accepted in target Journal"),
        (
            ACCEPTED_IN_ALTERNATIVE_AWAITING_PUBOFFER_ACCEPTANCE,
            "Accepted in alternative Journal; awaiting puboffer acceptance",
        ),
        (ACCEPTED_IN_ALTERNATIVE, "Accepted in alternative Journal"),
        (REJECTED, "Publication decision taken: reject"),
        (WITHDRAWN, "Withdrawn by the Authors"),
        (PUBLISHED, "Published"),
    )

    # Submissions which are currently under consideration
    UNDER_CONSIDERATION = (
        INCOMING,
        ADMISSIBLE,
        PREASSIGNMENT,
        SEEKING_ASSIGNMENT,
        REFEREEING_IN_PREPARATION,
        IN_REFEREEING,
        REFEREEING_CLOSED,
        AWAITING_RESUBMISSION,
        RESUBMITTED,
        VOTING_IN_PREPARATION,
        IN_VOTING,
        AWAITING_DECISION,
        ACCEPTED_IN_ALTERNATIVE_AWAITING_PUBOFFER_ACCEPTANCE,
    )

    STAGE_SLUGS = (  # for converters
        "incoming",
        "preassignment",
        "assignment",
        "refereeing_in_preparation",
        "in_refereeing",
        "decisionmaking",
        "in_production",
    )

    # Further handy sets
    STAGE_INCOMING = (INCOMING, ADMISSIBLE)
    STAGE_PREASSIGNMENT = (PREASSIGNMENT,)
    STAGE_ASSIGNMENT = (SEEKING_ASSIGNMENT,)
    STAGE_REFEREEING_IN_PREPARATION = (REFEREEING_IN_PREPARATION,)
    STAGE_IN_REFEREEING = (IN_REFEREEING,)
    STAGE_DECISIONMAKING = (
        REFEREEING_CLOSED,
        VOTING_IN_PREPARATION,
        IN_VOTING,
        AWAITING_DECISION,
        ACCEPTED_IN_ALTERNATIVE_AWAITING_PUBOFFER_ACCEPTANCE,
    )
    STAGE_DECIDED = (
        ADMISSION_FAILED,
        PREASSIGNMENT_FAILED,
        ASSIGNMENT_FAILED,
        AWAITING_RESUBMISSION,
        RESUBMITTED,
        ACCEPTED_IN_TARGET,
        ACCEPTED_IN_ALTERNATIVE,
        REJECTED,
        WITHDRAWN,
        PUBLISHED,
    )
    TREATED = (
        ACCEPTED_IN_TARGET,
        ACCEPTED_IN_ALTERNATIVE,
        REJECTED,
        WITHDRAWN,
        PUBLISHED,
    )
    STAGE_IN_PRODUCTION = (
        ACCEPTED_IN_TARGET,
        ACCEPTED_IN_ALTERNATIVE,
    )
    STAGE_INCOMING_COMPLETED_STATUSES = (
        STAGE_PREASSIGNMENT
        + STAGE_ASSIGNMENT
        + STAGE_REFEREEING_IN_PREPARATION
        + STAGE_IN_REFEREEING
        + STAGE_DECISIONMAKING
        + STAGE_DECIDED
    )
    STAGE_PREASSIGNMENT_COMPLETED_STATUSES = (
        STAGE_ASSIGNMENT
        + STAGE_REFEREEING_IN_PREPARATION
        + STAGE_IN_REFEREEING
        + STAGE_DECISIONMAKING
        + STAGE_DECIDED
    )
    STAGE_ASSIGNMENT_COMPLETED_STATUSES = (
        STAGE_REFEREEING_IN_PREPARATION
        + STAGE_IN_REFEREEING
        + STAGE_DECISIONMAKING
        + STAGE_DECIDED
    )
    STAGE_REFEREEING_IN_PREPARATION_COMPLETED_STATUSES = (
        STAGE_IN_REFEREEING + STAGE_DECISIONMAKING + STAGE_DECIDED
    )
    STAGE_IN_REFEREEING_COMPLETED_STATUSES = STAGE_DECISIONMAKING + STAGE_DECIDED

    # Related managers
    if TYPE_CHECKING:
        referee_invitations: "RelatedManager[RefereeInvitation]"
        author_profiles: "RelatedManager[SubmissionAuthorProfile]"
        collections: "RelatedManager[Collection]"
        editorial_assignments: "RelatedManager[EditorialAssignment]"
        reports: "RelatedManager[Report]"
        conditional_assignment_offers: "RelatedManager[ConditionalAssignmentOffer]"

    # Fields
    preprint = models.OneToOneField(
        "preprints.Preprint", on_delete=models.CASCADE, related_name="submission"
    )

    author_comments = models.TextField(blank=True)
    author_list = models.CharField(
        max_length=10000,
        verbose_name="author list",
        help_text=(
            "Please use full first names (we <strong>beg</strong> you!): "
            "<em>Abe Cee, Dee Efgee, Haich Idjay Kay</em>"
            "<br>(not providing full first names makes metadata handling "
            "unnecessarily work-intensive for us)"
        ),
    )

    # Ontology-based semantic linking
    acad_field = models.ForeignKey["AcademicField"](
        "ontology.AcademicField", on_delete=models.PROTECT, related_name="submissions"
    )
    specialties = models.ManyToManyField["Submission", "Specialty"](
        "ontology.Specialty", related_name="submissions"
    )
    topics = models.ManyToManyField["Submission", "Topic"]("ontology.Topic", blank=True)

    approaches = ChoiceArrayField(
        models.CharField(max_length=24, choices=SCIPOST_APPROACHES),
        blank=True,
        null=True,
    )
    editor_in_charge = models.ForeignKey["Contributor"](
        "scipost.Contributor",
        related_name="EIC",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    list_of_changes = models.TextField(blank=True)
    open_for_commenting = models.BooleanField(default=False)
    open_for_reporting = models.BooleanField(default=False)
    referees_flagged = models.TextField(blank=True)
    referees_suggested = models.TextField(blank=True)
    remarks_for_editors = models.TextField(blank=True)
    reporting_deadline = models.DateTimeField(null=True, blank=True, default=None)

    # Submission status fields
    status = models.CharField(
        max_length=30, choices=SUBMISSION_STATUSES, default=INCOMING
    )
    visible_public = models.BooleanField("Is publicly visible", default=False)
    visible_pool = models.BooleanField("Is visible in the Pool", default=False)
    on_hold = models.BooleanField(default=False)

    # Link to previous Submission, or existing bundle member
    is_resubmission_of = models.ForeignKey["Submission"](
        "self",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="successor",
    )
    thread_hash = models.UUIDField(default=uuid.uuid4)
    followup_of = models.ManyToManyField["Submission", "Publication"](
        "journals.Publication",
        blank=True,
        related_name="followups",
    )

    refereeing_cycle = models.CharField(
        max_length=30, choices=SUBMISSION_CYCLES, default=CYCLE_DEFAULT, blank=True
    )

    auto_updated_fellowship = models.BooleanField(default=True)
    fellows = models.ManyToManyField["Submission", "Fellowship"](
        "colleges.Fellowship", blank=True, related_name="pool"
    )

    submitted_by = models.ForeignKey["Contributor"](
        "scipost.Contributor",
        on_delete=models.CASCADE,
        related_name="submitted_submissions",
    )
    submitted_to = models.ForeignKey["Journal"](
        "journals.Journal", on_delete=models.CASCADE
    )
    proceedings = models.ForeignKey["Proceedings"](
        "proceedings.Proceedings",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="submissions",
        help_text=(
            "Don't find the Proceedings you are looking for? "
            "Ask the conference organizers to contact our admin "
            "to set things up."
        ),
    )

    title = models.CharField(max_length=300)

    # Authors which have been mapped to contributors:
    authors = models.ManyToManyField["Submission", "Contributor"](
        "scipost.Contributor", blank=True, related_name="submissions"
    )
    authors_claims = models.ManyToManyField["Submission", "Contributor"](
        "scipost.Contributor", blank=True, related_name="claimed_submissions"
    )
    authors_false_claims = models.ManyToManyField["Submission", "Contributor"](
        "scipost.Contributor", blank=True, related_name="false_claimed_submissions"
    )
    abstract = models.TextField()

    # Links to associated code and data
    data_repository_url = models.URLField(
        blank=True, help_text="Link to a data repository pertaining to your manuscript"
    )
    code_repository_url = models.URLField(
        blank=True, help_text="Link to a code repository pertaining to your manuscript"
    )
    code_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Information about the software referenced in the codebases publication",
    )

    fulfilled_expectations = models.CharField(default=str, max_length=1000, blank=True)

    # Comments can be added to a Submission
    comments = GenericRelation("comments.Comment", related_query_name="submissions")

    # Conflicts of interest
    needs_conflicts_update = models.BooleanField(default=True)

    # Plagiarism
    internal_plagiarism_matches = models.JSONField(
        default=dict,
        blank=True,
        null=True,
    )
    iThenticate_plagiarism_report = models.OneToOneField["iThenticateReport"](
        "submissions.iThenticateReport",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="to_submission",
    )

    # Refereeing pack
    pdf_refereeing_pack = models.FileField(
        upload_to="UPLOADS/REFEREE/%Y/%m/", max_length=200, blank=True
    )

    # Metadata
    metadata = models.JSONField(default=dict, blank=True, null=True)
    submission_date = models.DateTimeField(
        verbose_name="submission date", default=timezone.now
    )
    checks_cleared_date = models.DateTimeField(
        verbose_name="checks cleared date", null=True, blank=True
    )
    eic_first_assigned_date = models.DateTimeField(
        verbose_name="EIC first assigned date", null=True, blank=True
    )
    acceptance_date = models.DateField(
        verbose_name="acceptance date", null=True, blank=True
    )
    completion_date = models.DateField(
        verbose_name="completion date", null=True, blank=True
    )
    assignment_deadline = models.DateField(
        verbose_name="assignment deadline", null=True, blank=True
    )
    latest_activity = models.DateTimeField(auto_now=True)
    update_search_index = models.BooleanField(default=True)

    objects = SubmissionQuerySet.as_manager()

    # Temporary
    invitation_order = models.IntegerField(default=0)

    red_flags = GenericRelation(
        "ethics.RedFlag",
        object_id_field="concerning_object_id",
        content_type_field="concerning_object_type",
        related_query_name="submission",
    )

    class Meta:
        app_label = "submissions"
        ordering = ["-submission_date"]
        permissions = [
            ("take_edadmin_actions", "Take editorial admin actions"),
            ("view_edadmin_info", "View editorial admin information"),
        ]

    def save(self, *args, **kwargs):
        """Prefill some fields before saving."""
        obj = super().save(*args, **kwargs)
        if hasattr(self, "cycle"):
            self.set_cycle()
        return obj

    def __str__(self):
        """Summarize the Submission in a string."""
        header = "{identifier}, {title} by {authors}".format(
            identifier=self.preprint.identifier_w_vn_nr,
            title=self.title[:30],
            authors=self.author_list[:30],
        )
        if self.is_latest:
            header += " (current version)"
        else:
            header += " (deprecated version " + str(self.thread_sequence_order) + ")"
        if hasattr(self, "publication") and self.publication.is_published:
            header += " (published as %s (%s))" % (
                self.publication.doi_string,
                self.publication.publication_date.strftime("%Y"),
            )
        return header

    ##########################################
    # Shortcut properties for stage checking #
    ##########################################
    @property
    def in_stage_incoming(self):
        return self.status in self.STAGE_INCOMING

    @property
    def stage_incoming_completed(self):
        return self.status in self.STAGE_INCOMING_COMPLETED_STATUSES

    @property
    def in_stage_preassignment(self):
        return self.status in self.STAGE_PREASSIGNMENT

    @property
    def stage_preassignment_completed(self):
        return self.status in self.STAGE_PREASSIGNMENT_COMPLETED_STATUSES

    @property
    def in_stage_assignment(self):
        return self.status in self.STAGE_ASSIGNMENT

    @property
    def stage_assignment_completed(self):
        return self.status in self.STAGE_ASSIGNMENT_COMPLETED_STATUSES

    @property
    def in_stage_refereeing_in_preparation(self):
        return self.status in self.STAGE_REFEREEING_IN_PREPARATION

    @property
    def stage_refereeing_in_preparation_completed(self):
        return self.status in self.STAGE_REFEREEING_IN_PREPARATION_COMPLETED_STATUSES

    @property
    def in_stage_in_refereeing(self):
        return self.status in self.STAGE_IN_REFEREEING

    @property
    def stage_in_refereeing_completed(self):
        return self.status in self.STAGE_IN_REFEREEING_COMPLETED_STATUSES

    @property
    def in_stage_decisionmaking(self):
        return self.status in self.STAGE_DECISIONMAKING

    @property
    def stage_decisionmaking_completed_statuses(self):  # include for completeness
        return self.STAGE_DECIDED

    @property
    def stage_decisionmaking_completed(self):
        return self.in_stage_decided

    @property
    def in_stage_decided(self):
        return self.status in self.STAGE_DECIDED

    @property
    def treated(self):
        return self.status in self.TREATED

    @property
    def in_stage_in_production(self):
        return self.status in self.STAGE_IN_PRODUCTION

    @property
    def stage(self):
        if self.in_stage_incoming:
            return "incoming"
        elif self.in_stage_preassignment:
            return "preassignment"
        elif self.in_stage_assignment:
            return "assignment"
        elif self.in_stage_refereeing_in_preparation:
            return "refereeing_in_preparation"
        elif self.in_stage_in_refereeing:
            return "in_refereeing"
        elif self.in_stage_decisionmaking:
            return "decisionmaking"
        elif self.in_stage_decided:
            return "decided"
        elif self.in_stage_treated:
            return "treated"
        elif self.in_stage_in_production:
            return "in_production"
        raise StageNotDefinedError

    @property
    def get_stage_display(self):
        if self.in_stage_incoming:
            return "Incoming"
        elif self.in_stage_preassignment:
            return "Preassignment"
        elif self.in_stage_assignment:
            return "Assignment"
        elif self.in_stage_refereeing_in_preparation:
            return "Refereeing in preparation"
        elif self.in_stage_in_refereeing:
            return "In refereeing"
        elif self.in_stage_decisionmaking:
            return "Decisionmaking"
        elif self.in_stage_decided:
            return "Decided"
        elif self.in_stage_treated:
            return "Treated"
        elif self.in_stage_in_production:
            return "In production"
        raise StageNotDefinedError

    ###############################################
    # End shortucut properties for stage checking #
    ###############################################

    @cached_property
    def is_latest(self):
        return self == self.get_latest_version()

    @property
    def authors_as_list(self):
        """Returns a python list of the authors, extracted from author_list field."""
        comma_separated = self.author_list.replace(", and", ", ")
        comma_separated = comma_separated.replace(" and ", ", ")
        comma_separated = comma_separated.replace(", & ", ", ")
        comma_separated = comma_separated.replace(" & ", ", ")
        comma_separated = comma_separated.replace(";", ", ")
        return [e.lstrip().rstrip() for e in comma_separated.split(",")]

    def touch(self):
        """Update latest activity timestamp."""
        Submission.objects.filter(id=self.id).update(latest_activity=timezone.now())

    def comments_set_complete(self):
        """Return Comments on Submissions, Reports and other Comments."""
        qs = Comment.objects.filter(
            Q(submissions=self)
            | Q(reports__submission=self)
            | Q(comments__reports__submission=self)
            | Q(comments__submissions=self)
        )
        # Add recursive comments:
        for c in qs:
            if c.nested_comments:
                qs = qs | c.all_nested_comments().all()
        return qs.distinct()

    @property
    def cycle(self) -> ShortCycle | DirectCycle | RegularCycle:
        """Get cycle object relevant for the Submission."""
        if not hasattr(self, "_cycle"):
            self.set_cycle()
        return self._cycle

    def set_cycle(self):
        """Set cycle to the Submission on request."""
        if self.refereeing_cycle == CYCLE_SHORT:
            self._cycle = ShortCycle(self)
        elif self.refereeing_cycle == CYCLE_DIRECT_REC:
            self._cycle = DirectCycle(self)
        else:
            self._cycle = RegularCycle(self)

    def reset_refereeing_cycle(self):
        """
        Reset the submission's refereeing cycle:
        - Set the refereeing cycle to the undetermined state if it a resubmission, otherwise to the default cycle
        - Set the submission status to refereeing in preparation
        """
        self._cycle = None
        self.status = self.REFEREEING_IN_PREPARATION
        self.refereeing_cycle = (
            CYCLE_UNDETERMINED if self.is_resubmission else CYCLE_DEFAULT
        )
        self.save()

    def get_absolute_url(self):
        """Return url of the Submission detail page."""
        return reverse(
            "submissions:submission", args=(self.preprint.identifier_w_vn_nr,)
        )

    def get_fulfilled_expectations_display(self) -> list[str]:
        """Return a list of fulfilled expectation displays"""
        return [
            display
            for key, display in self.submitted_to.expectations
            if key in self.fulfilled_expectations.split(",")
        ]

    @property
    def is_resubmission(self):
        return self.is_resubmission_of is not None

    @property
    def plagiarism_internal_tests_completed(self):
        from submissions.models import InternalPlagiarismAssessment

        try:
            return (
                self.internal_plagiarism_assessment.passed
                or self.internal_plagiarism_assessment.failed
            )
        except InternalPlagiarismAssessment.DoesNotExist:
            return False

    @property
    def plagiarism_iThenticate_tests_completed(self):
        from submissions.models import iThenticatePlagiarismAssessment

        try:
            return (
                self.iThenticate_plagiarism_assessment.passed
                or self.iThenticate_plagiarism_assessment.failed
            )
        except iThenticatePlagiarismAssessment.DoesNotExist:
            return False

    @property
    def plagiarism_tests_completed(self):
        return (
            self.plagiarism_internal_tests_completed
            and self.plagiarism_iThenticate_tests_completed
        )

    @property
    def all_authors_have_matching_profiles(self):
        return self.author_profiles.filter(profile__isnull=False).count() == len(
            self.authors_as_list
        )

    @property
    def preassignment_tasks_done(self):
        return self.all_authors_have_matching_profiles

    @property
    def recommendation(self):
        return self.eicrecommendations.active().first()

    @property
    def eic_recommendation_required(self):
        """Return if Submission requires a EICRecommendation to be formulated."""
        return not self.eicrecommendations.active().exists()

    @property
    def revision_requested(self):
        """Check if Submission has fixed EICRecommendation asking for revision."""
        return self.eicrecommendations.fixed().asking_revision().exists()

    @property
    def under_consideration(self):
        """
        Check if the Submission is currently under consideration
        (in other words: is undergoing editorial processing).
        """
        return self.status in self.UNDER_CONSIDERATION

    @property
    def open_for_resubmission(self):
        """Check if Submission has fixed EICRecommendation asking for revision."""
        return self.status == self.AWAITING_RESUBMISSION

    @property
    def has_extended_assignment_deadline(self):
        """
        Check if Submission has had its assignment deadline extended, by looking for the corresponding event.
        """
        return self.events.filter(
            text__icontains="assignment deadline",
            text__contains="extended",
        ).exists()

    @property
    def reporting_deadline_has_passed(self):
        """Check if Submission has passed its reporting deadline."""
        if self.reporting_deadline is None:
            return False
        return timezone.now() > self.reporting_deadline

    @property
    def reporting_deadline_approaching(self):
        """Check if reporting deadline is within 7 days from now but not passed yet."""
        if self.reporting_deadline is None:
            return False

        if self.status != self.IN_REFEREEING:
            # These statuses do not have a deadline
            return False

        if self.reporting_deadline_has_passed:
            return False
        return timezone.now() > self.reporting_deadline - datetime.timedelta(days=7)

    @property
    def is_open_for_reporting_within_deadline(self):
        """Check if Submission is open for reporting and within deadlines."""
        return self.open_for_reporting and not self.reporting_deadline_has_passed

    @property
    def submission_date_ymd(self):
        """Return the submission date in YYYY-MM-DD format."""
        return self.submission_date.date()

    @property
    def original_submission_date_ymd(self):
        """Return the submission date in YYYY-MM-DD format."""
        return self.original_submission_date.date()

    @property
    def original_submission_date(self):
        """Return the submission_date of the first Submission in the thread."""
        return (
            Submission.objects.filter(
                thread_hash=self.thread_hash, is_resubmission_of__isnull=True
            )
            .first()
            .submission_date
        )

    @property
    def can_reset_reporting_deadline(self):
        """Check if reporting deadline is allowed to be reset."""
        if self.status in self.STAGE_DECIDED:
            return False

        if self.refereeing_cycle == CYCLE_DIRECT_REC:
            # This cycle doesn't have a formal refereeing round.
            return False

        return self.editor_in_charge is not None

    @property
    def nr_unique_thread_vetted_reports(self):
        """Return the number of vetted reports from the set of latest reports submitted by each author."""
        # REFACTOR: I don't have access to Report objects here, so I have to be creative
        thread_reports = self.thread_full.filter(reports__isnull=False).values(
            "reports__status", "reports__author", "reports__date_submitted"
        )
        latest_reports = {}
        for report in thread_reports:
            if report["reports__author"] not in latest_reports:
                latest_reports[report["reports__author"]] = report
            elif (
                report["reports__date_submitted"]
                > latest_reports[report["reports__author"]]["reports__date_submitted"]
            ):
                latest_reports[report["reports__author"]] = report

        vetted_reports = sum(
            [
                report["reports__status"] == STATUS_VETTED
                for report in latest_reports.values()
            ]
        )
        return vetted_reports

    @property
    def thread_full(self):
        """Return all Submissions in the database in this thread."""
        return Submission.objects.filter(thread_hash=self.thread_hash).order_by(
            "-submission_date", "preprint"
        )

    @property
    def thread(self):
        """Return all (public) Submissions in the database in this thread."""
        return (
            Submission.objects.public()
            .filter(thread_hash=self.thread_hash)
            .order_by("-submission_date", "preprint")
        )

    @cached_property
    def thread_sequence_order(self):
        """Return the ordering of this Submission within its thread."""
        return self.thread.filter(submission_date__lt=self.submission_date).count() + 1

    @cached_property
    def other_versions(self):
        """Return other Submissions in the database in this thread."""
        return self.get_other_versions().order_by("-submission_date", "preprint")

    def get_other_versions(self):
        """Return queryset of other Submissions with this thread."""
        return Submission.objects.filter(thread_hash=self.thread_hash).exclude(
            pk=self.id
        )

    def get_latest_version(self):
        """Return the latest version in the thread of this Submission."""
        return self.thread_full.first()

    def get_latest_public_version(self):
        """Return the latest publicly-visible version in the thread of this Submission."""
        return self.thread.first()

    def _add_event(self, sort, message):
        event = SubmissionEvent(submission=self, event=sort, text=message)
        event.save()

    def add_general_event(self, message):
        """Generate message meant for EdAdmin, EIC and authors."""
        self._add_event(EVENT_GENERAL, message)

    def add_event_for_edadmin(self, message):
        """Generate message meant for EdAdmin only."""
        self._add_event(EVENT_FOR_EDADMIN, message)

    def add_event_for_eic(self, message):
        """Generate message meant for EIC and Editorial Administration only."""
        self._add_event(EVENT_FOR_EIC, message)

    def add_event_for_author(self, message):
        """Generate message meant for authors only."""
        self._add_event(EVENT_FOR_AUTHOR, message)

    def flag_coauthorships_arxiv(self, fellows):
        """Identify coauthorships from arXiv, using author surname matching."""
        coauthorships = {}
        if self.metadata and "entries" in self.metadata:
            author_last_names = []
            for author in self.metadata["entries"][0]["authors"]:
                # Gather author data to do conflict-of-interest queries with
                author_last_names.append(author["name"].split()[-1])
            authors_last_names_str = "+OR+".join(author_last_names)

            for fellow in fellows:
                # For each fellow found, so a query with the authors to check for conflicts
                search_query = "au:({fellow}+AND+({authors}))".format(
                    fellow=fellow.contributor.user.last_name,
                    authors=authors_last_names_str,
                )
                queryurl = (
                    "https://export.arxiv.org/api/query?search_query={sq}".format(
                        sq=search_query
                    )
                )
                queryurl += "&sortBy=submittedDate&sortOrder=descending&max_results=5"
                queryurl = queryurl.replace(
                    " ", "+"
                )  # Fallback for some last names with spaces
                queryresults = feedparser.parse(queryurl)
                if queryresults.entries:
                    coauthorships[fellow.contributor.user.last_name] = (
                        queryresults.entries
                    )
        return coauthorships

    def is_sending_editorial_invitations(self):
        """Return whether editorial assignments are being sent out."""
        if self.status != self.SEEKING_ASSIGNMENT:
            return False

        return self.editorial_assignments.preassigned().exists()

    def eic_not_in_fellowship(self):
        """
        Check whether the EIC is actually in the fellowship of the Submission.
        """
        if not self.editor_in_charge:
            # None assigned yet.
            return False

        contributors_ids = Contributor.objects.filter(
            fellowships__pool=self
        ).values_list("id", flat=True)
        return self.editor_in_charge.id not in contributors_ids

    def set_editor_in_charge(
        self, eic: Contributor | None, commit: bool = True
    ) -> None:
        """
        Set the Editor-in-Charge of the Submission.
        If `eic` is `None`, the EIC will be removed.
        Also updates the following:
            - Add permission to the new EIC to vet comments.

        Args:
            eic: The new Editor-in-Charge.
            commit: Whether to save the changes to the database.
        """
        old_editor = self.editor_in_charge
        editor_changed = old_editor != eic

        # If the EIC has not changed, return early
        if not editor_changed:
            return

        # Add permission to new EIC, remove from old EIC if replaced
        if isinstance(eic, Contributor):
            assign_perm("comments.can_vet_comments", eic.user, self.comments.all())
        if old_editor:
            remove_perm(
                "comments.can_vet_comments", old_editor.user, self.comments.all()
            )

        self.editor_in_charge = eic

        # Add appropriate event for EdAdmin
        if isinstance(eic, Contributor):
            self.add_event_for_edadmin(
                f"Editor-in-Charge {eic} has been assigned to the Submission"
                + f", replacing {old_editor}."
                if old_editor
                else "."
            )
        elif eic is None:
            self.add_event_for_edadmin(
                f"Editor-in-Charge {old_editor} has been removed from the Submission."
            )

        if commit:
            self.save()

    def get_default_fellowship(self):
        """
        Return the default *list* of Fellows for this Submission.
        - For a regular Submission, this is the subset of Fellowships of the Editorial College
        which have at least one Specialty in common with the Submission.
        - For a Proceedings Submission, this is the guest Editor of the Proceedings.
        """
        fellows = (
            Fellowship.objects.active()
            .without_competing_interests_against_submission_authors_of(self)
            .without_authorship_of_submission(self)
        )

        if self.proceedings:
            # Add only Proceedings-related Fellowships
            fellows = fellows.filter(proceedings=self.proceedings)
        elif self.collections.all():
            # Add the Fellowships of the collections
            fellows = fellows.filter(
                id__in=self.collections.all().values("expected_editors")
            )
        else:
            # Add only Fellowships from the same College and with matching specialties
            fellows = fellows.college_specialties_overlap_with_submission(self)

            # As a special rule, MigPol only wants Senior Fellows to be assigned
            if self.submitted_to.name == "Migration Politics":
                fellows = fellows.senior()
            else:
                fellows = fellows.regular_or_senior()

        return fellows.distinct()

    @property
    def editorial_decision(self) -> "EditorialDecision | None":
        """Returns the latest EditorialDecision (if it exists)."""
        if self.editorialdecision_set.nondeprecated().exists():
            return self.editorialdecision_set.nondeprecated().latest_version()
        return None

    def edadmin_notes(self):
        """Notes to be displayed to edadmin."""
        notes: list[tuple[str, str]] = []

        if nr_remarks := self.remarks.count():
            notes.append(
                (
                    "info",
                    f"There are {nr_remarks} remarks for this submission.",
                )
            )

        return notes


# The next two models are for optimization of django guardian object-level permissions
# using direct foreign keys instead of generic ones
# (see https://django-guardian.readthedocs.io/en/stable/userguide/performance.html)


class SubmissionUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Submission, on_delete=models.CASCADE)


class SubmissionGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Submission, on_delete=models.CASCADE)


class SubmissionEvent(SubmissionRelatedObjectMixin, TimeStampedModel):
    """Private message directly related to a Submission.

    The SubmissionEvent's goal is to act as a messaging model for the Submission cycle.
    Its main audience will be the author(s) and the Editor-in-charge of a Submission.

    Be aware that both the author and editor-in-charge will read the submission event.
    Make sure the right text is given to the appropriate event-type, to protect
    the fellow's identity.
    """

    submission = models.ForeignKey(
        "submissions.Submission", on_delete=models.CASCADE, related_name="events"
    )
    event = models.CharField(max_length=4, choices=EVENT_TYPES, default=EVENT_GENERAL)
    text = models.TextField()

    objects = SubmissionEventQuerySet.as_manager()

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        """Summarize the SubmissionEvent's meta information."""
        return "%s: %s" % (str(self.submission), self.get_event_display())


class SubmissionTiering(models.Model):
    """A Fellow's quality tiering of a Submission for a given Journal, given during voting."""

    submission = models.ForeignKey(
        "submissions.Submission", on_delete=models.CASCADE, related_name="tierings"
    )
    fellow = models.ForeignKey("scipost.Contributor", on_delete=models.CASCADE)
    for_journal = models.ForeignKey("journals.Journal", on_delete=models.CASCADE)
    tier = models.SmallIntegerField(choices=SUBMISSION_TIERS)
