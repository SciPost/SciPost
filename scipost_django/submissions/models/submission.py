__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
import feedparser
import uuid

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property

from guardian.models import UserObjectPermissionBase
from guardian.models import GroupObjectPermissionBase

from scipost.behaviors import TimeStampedModel
from scipost.constants import SCIPOST_APPROACHES
from scipost.fields import ChoiceArrayField
from scipost.models import Contributor

from comments.models import Comment

from ..behaviors import SubmissionRelatedObjectMixin
from ..constants import (
    STATUS_PREASSIGNED,
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
)
from ..managers import SubmissionQuerySet, SubmissionEventQuerySet
from ..refereeing_cycles import ShortCycle, DirectCycle, RegularCycle


class Submission(models.Model):
    """
    A Submission is a preprint sent to SciPost for consideration.
    """

    # Possible statuses
    INCOMING = "incoming"
    ADMISSION_FAILED = "admission_failed"
    PREASSIGNMENT = "preassignment"
    PREASSIGNMENT_FAILED = "preassignment_failed"
    SEEKING_ASSIGNMENT = "seeking_assignment" # new2
    ASSIGNMENT_FAILED = "assignment_failed" # remove # new2 reinstate
    REFEREEING_IN_PREPARATION = "refereeing_in_preparation"
    IN_REFEREEING = "in_refereeing"
    REFEREEING_CLOSED = "refereeing_closed"
    AWAITING_RESUBMISSION = "awaiting_resubmission"
    RESUBMITTED = "resubmitted"
    VOTING_IN_PREPARATION = "voting_in_preparation"
    IN_VOTING = "in_voting"
    AWAITING_DECISION = "awaiting_decision"
    ACCEPTED = "accepted" # remove
    ACCEPTED_IN_TARGET = "accepted_in_target"
    ACCEPTED_IN_ALTERNATIVE_AWAITING_PUBOFFER_ACCEPTANCE = "accepted_alt_puboffer_waiting"
    ACCEPTED_IN_ALTERNATIVE = "accepted_alt"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    PUBLISHED = "published"

    SUBMISSION_STATUSES = (
        (INCOMING, "Submission incoming, awaiting EdAdmin"),
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

    # Further handy sets
    STAGE_INCOMING = (INCOMING, ADMISSION_FAILED)
    STAGE_PREASSIGNMENT = (PREASSIGNMENT, PREASSIGNMENT_FAILED)
    STAGE_ASSIGNMENT = (SEEKING_ASSIGNMENT, ASSIGNMENT_FAILED)
    STAGE_REFEREEING_IN_PREPARATION = (REFEREEING_IN_PREPARATION,)
    STAGE_IN_REFEREEING = (IN_REFEREEING, REFEREEING_CLOSED)
    STAGE_DECISIONMAKING = (
        VOTING_IN_PREPARATION,
        IN_VOTING,
        AWAITING_DECISION,
        ACCEPTED_IN_ALTERNATIVE_AWAITING_PUBOFFER_ACCEPTANCE,
    )
    STAGE_DECIDED = (
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
    # Fields
    preprint = models.OneToOneField(
        "preprints.Preprint", on_delete=models.CASCADE, related_name="submission"
    )

    author_comments = models.TextField(blank=True)
    author_list = models.CharField(max_length=10000, verbose_name="author list")

    # Ontology-based semantic linking
    acad_field = models.ForeignKey(
        "ontology.AcademicField", on_delete=models.PROTECT, related_name="submissions"
    )
    specialties = models.ManyToManyField(
        "ontology.Specialty", related_name="submissions"
    )
    topics = models.ManyToManyField("ontology.Topic", blank=True)

    approaches = ChoiceArrayField(
        models.CharField(max_length=24, choices=SCIPOST_APPROACHES),
        blank=True,
        null=True,
        verbose_name="approach(es) [optional]",
    )
    editor_in_charge = models.ForeignKey(
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
    reporting_deadline = models.DateTimeField(default=timezone.now)

    # Submission status fields
    status = models.CharField(
        max_length=30, choices=SUBMISSION_STATUSES, default=INCOMING
    )
    visible_public = models.BooleanField("Is publicly visible", default=False)
    visible_pool = models.BooleanField("Is visible in the Pool", default=False)
    is_resubmission_of = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="successor",
    )
    thread_hash = models.UUIDField(default=uuid.uuid4)
    refereeing_cycle = models.CharField(
        max_length=30, choices=SUBMISSION_CYCLES, default=CYCLE_DEFAULT, blank=True
    )

    fellows = models.ManyToManyField(
        "colleges.Fellowship", blank=True, related_name="pool"
    )

    submitted_by = models.ForeignKey(
        "scipost.Contributor",
        on_delete=models.CASCADE,
        related_name="submitted_submissions",
    )
    submitted_to = models.ForeignKey("journals.Journal", on_delete=models.CASCADE)
    proceedings = models.ForeignKey(
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
    authors = models.ManyToManyField(
        "scipost.Contributor", blank=True, related_name="submissions"
    )
    authors_claims = models.ManyToManyField(
        "scipost.Contributor", blank=True, related_name="claimed_submissions"
    )
    authors_false_claims = models.ManyToManyField(
        "scipost.Contributor", blank=True, related_name="false_claimed_submissions"
    )
    abstract = models.TextField()

    # Links to associated code and data
    code_repository_url = models.URLField(
        blank=True, help_text="Link to a code repository pertaining to your manuscript"
    )
    data_repository_url = models.URLField(
        blank=True, help_text="Link to a data repository pertaining to your manuscript"
    )

    # Comments can be added to a Submission
    comments = GenericRelation("comments.Comment", related_query_name="submissions")

    # iThenticate and conflicts
    needs_conflicts_update = models.BooleanField(default=True)
    plagiarism_report = models.OneToOneField(
        "submissions.iThenticateReport",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="to_submission",
    )
    internal_plagiarism_matches = models.JSONField(
        default=dict,
        blank=True,
        null=True,
    )

    pdf_refereeing_pack = models.FileField(
        upload_to="UPLOADS/REFEREE/%Y/%m/", max_length=200, blank=True
    )

    # Metadata
    metadata = models.JSONField(default=dict, blank=True, null=True)
    submission_date = models.DateTimeField(
        verbose_name="submission date", default=timezone.now
    )
    acceptance_date = models.DateField(
        verbose_name="acceptance date", null=True, blank=True
    )
    latest_activity = models.DateTimeField(auto_now=True)
    update_search_index = models.BooleanField(default=True)

    objects = SubmissionQuerySet.as_manager()

    # Temporary
    invitation_order = models.IntegerField(default=0)

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
    def stage_incoming_completed_statuses(self):
        return (
            self.STAGE_PREASSIGNMENT +
            self.STAGE_ASSIGNMENT +
            self.STAGE_REFEREEING_IN_PREPARATION +
            self.STAGE_IN_REFEREEING +
            self.STAGE_DECISIONMAKING +
            self.STAGE_DECIDED
        )

    @property
    def stage_incoming_completed(self):
        return self.status in self.stage_incoming_completed_statuses

    @property
    def in_stage_preassignment(self):
        return self.status in self.STAGE_PREASSIGNMENT

    @property
    def stage_preassignment_completed_statuses(self):
        return (
            self.STAGE_ASSIGNMENT +
            self.STAGE_REFEREEING_IN_PREPARATION +
            self.STAGE_IN_REFEREEING +
            self.STAGE_DECISIONMAKING +
            self.STAGE_DECIDED
        )

    @property
    def stage_preassignment_completed(self):
        return self.status in self.stage_preassignment_completed_statuses

    @property
    def in_stage_assignment(self):
        return self.status in self.STAGE_ASSIGNMENT

    @property
    def stage_assignment_completed_statuses(self):
        return (
            self.STAGE_REFEREEING_IN_PREPARATION +
            self.STAGE_IN_REFEREEING +
            self.STAGE_DECISIONMAKING +
            self.STAGE_DECIDED
        )

    @property
    def stage_assignment_completed(self):
        return self.status in self.stage_assignment_completed_statuses

    @property
    def in_stage_refereeing_in_preparation(self):
        return self.status in self.STAGE_REFEREEING_IN_PREPARATION

    @property
    def stage_refereeing_in_preparation_completed_statuses(self):
        return (
            self.STAGE_IN_REFEREEING +
            self.STAGE_DECISIONMAKING +
            self.STAGE_DECIDED
        )

    @property
    def stage_refereeing_in_preparation_completed(self):
        return self.status in self.stage_refereeing_in_preparation_completed_statuses

    @property
    def in_stage_in_refereeing(self):
        return self.status in self.STAGE_IN_REFEREEING

    @property
    def stage_in_refereeing_completed_statuses(self):
        return (
            self.STAGE_DECISIONMAKING +
            self.STAGE_DECIDED
        )

    @property
    def stage_in_refereeing_completed(self):
        return self.status in self.stage_in_refereeing_completed_statuses

    @property
    def in_stage_decisionmaking(self):
        return self.status in self.STAGE_DECISIONMAKING

    @property
    def stage_decisionmaking_completed_statuses(self): # include for completeness
        return self.STAGE_DECIDED

    @property
    def stage_decisionmaking_completed(self):
        return self.in_stage_decided

    @property
    def in_stage_decided(self):
        return self.status in self.STAGE_DECIDED
    ###############################################
    # End shortucut properties for stage checking #
    ###############################################


    @property
    def is_latest(self):
        return self.status != self.RESUBMITTED

    @property
    def authors_as_list(self):
        """Returns a python list of the authors, extracted from author_list field."""
        # Start by separating in comma's
        comma_separated = self.author_list.split(",")
        authors_as_list = []
        for entry in comma_separated:
            and_separated = entry.split(" and ")
            for subentry in and_separated:
                authors_as_list.append(subentry.lstrip().rstrip())
        return authors_as_list

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
    def cycle(self):
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

    def get_absolute_url(self):
        """Return url of the Submission detail page."""
        return reverse(
            "submissions:submission", args=(self.preprint.identifier_w_vn_nr,)
        )

    @property
    def is_resubmission(self):
        return self.is_resubmission_of is not None

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
    def reporting_deadline_has_passed(self):
        """Check if Submission has passed its reporting deadline."""
        return timezone.now() > self.reporting_deadline

    @property
    def reporting_deadline_approaching(self):
        """Check if reporting deadline is within 7 days from now but not passed yet."""
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
        if self.status in STAGE_DECIDED:
            return False

        if self.refereeing_cycle == CYCLE_DIRECT_REC:
            # This cycle doesn't have a formal refereeing round.
            return False

        return self.editor_in_charge is not None

    @property
    def thread_full(self):
        """Return all Submissions in the database in this thread."""
        return Submission.objects.filter(thread_hash=self.thread_hash).order_by(
            "-submission_date", "-preprint"
        )

    @property
    def thread(self):
        """Return all (public) Submissions in the database in this thread."""
        return (
            Submission.objects.public()
            .filter(thread_hash=self.thread_hash)
            .order_by("-submission_date", "-preprint")
        )

    @cached_property
    def thread_sequence_order(self):
        """Return the ordering of this Submission within its thread."""
        return self.thread.filter(submission_date__lt=self.submission_date).count() + 1

    @cached_property
    def other_versions(self):
        """Return other Submissions in the database in this thread."""
        return self.get_other_versions().order_by("-submission_date", "-preprint")

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
                    coauthorships[
                        fellow.contributor.user.last_name
                    ] = queryresults.entries
        return coauthorships

    def is_sending_editorial_invitations(self):
        """Return whether editorial assignments are being sent out."""
        if self.status != self.SEEKING_ASSIGNMENT:
            return False

        return self.editorial_assignments.filter(status=STATUS_PREASSIGNED).exists()

    def has_inadequate_fellowship_composition(self):
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

    @property
    def editorial_decision(self):
        """Returns the latest EditorialDecision (if it exists)."""
        if self.editorialdecision_set.nondeprecated().exists():
            return self.editorialdecision_set.nondeprecated().latest_version()
        return None


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
