__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import abc
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property

from common.utils.text import space_uppercase
from journals.models.journal import Journal
from mails.utils import DirectMailUtil
from submissions.constants import CYCLE_DEFAULT
from submissions.managers.assignment import ConditionalAssignmentOfferQuerySet

from ..behaviors import SubmissionRelatedObjectMixin
from ..managers import EditorialAssignmentQuerySet

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from submissions.models import Submission
    from scipost.models import Contributor


class EditorialAssignment(SubmissionRelatedObjectMixin, models.Model):
    """
    Consideration of a Fellow to become Editor-in-Charge of a Submission.
    """

    REFUSE_OUTSIDE_EXPERTISE = "OFE"
    REFUSE_TOO_BUSY = "BUS"
    REFUSE_ON_VACATION = "VAC"
    REFUSE_COI_COAUTHOR = "COI"
    REFUSE_COI_COLLEAGUE = "CCC"
    REFUSE_COI_COMPETITOR = "CCM"
    REFUSE_COI_OTHER = "COT"
    REFUSE_NOT_IMPARTIAL = "NIR"
    REFUSE_NOT_INTERESTED = "NIE"
    REFUSE_DESK_REJECT = "DNP"
    REFUSE_OTHER = "OTH"
    REFUSAL_REASONS = (
        (REFUSE_OUTSIDE_EXPERTISE, "Outside of my field of expertise"),
        (REFUSE_TOO_BUSY, "Too busy"),
        (REFUSE_ON_VACATION, "Away on vacation"),
        (REFUSE_COI_COAUTHOR, "Conflict of interest: coauthor in last 5 years"),
        (REFUSE_COI_COLLEAGUE, "Conflict of interest: close colleague"),
        (REFUSE_COI_COMPETITOR, "Conflict of interest: close competitor"),
        (REFUSE_COI_OTHER, "Conflict of interest: other"),
        (REFUSE_NOT_IMPARTIAL, "Cannot give an impartial assessment"),
        (REFUSE_NOT_INTERESTED, "Not interested enough"),
        (
            REFUSE_DESK_REJECT,
            "SciPost should desk reject this paper",
        ),
        (REFUSE_OTHER, "Other"),
    )

    STATUS_PREASSIGNED = "preassigned"
    STATUS_INVITED = "invited"
    STATUS_ACCEPTED = "accepted"
    STATUS_ACCEPT_IF_NOBODY_ELSE = "accifnobodyelse"
    STATUS_ACCEPT_IF_TRANSFERRED = "acciftransferred"
    STATUS_PERHAPS_LATER = "askagainlater"
    STATUS_DECLINED = "declined"
    STATUS_COMPLETED = "completed"
    STATUS_DEPRECATED = "deprecated"
    STATUS_REPLACED = "replaced"
    ASSIGNMENT_STATUSES = (
        (STATUS_PREASSIGNED, "Preassigned"),
        (STATUS_INVITED, "Invited"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_ACCEPT_IF_NOBODY_ELSE, "Accept (if nobody else does)"),
        (
            STATUS_ACCEPT_IF_TRANSFERRED,
            "Accept (if transferred to non-flagship journal)",
        ),
        (STATUS_PERHAPS_LATER, "Perhaps; ask again later"),
        (STATUS_DECLINED, "Declined"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_DEPRECATED, "Deprecated"),
        (STATUS_REPLACED, "Replaced"),
    )

    submission = models.ForeignKey(
        "submissions.Submission",
        on_delete=models.CASCADE,
    )

    to = models.ForeignKey("scipost.Contributor", on_delete=models.CASCADE)

    status = models.CharField(
        max_length=16, choices=ASSIGNMENT_STATUSES, default=STATUS_PREASSIGNED
    )
    refusal_reason = models.CharField(
        max_length=3, choices=REFUSAL_REASONS, blank=True, null=True
    )
    invitation_order = models.PositiveSmallIntegerField(default=0)

    date_created = models.DateTimeField(default=timezone.now)
    date_invited = models.DateTimeField(blank=True, null=True)
    date_answered = models.DateTimeField(blank=True, null=True)

    objects = EditorialAssignmentQuerySet.as_manager()

    class Meta:
        default_related_name = "editorial_assignments"
        ordering = ["-date_created"]

    def __str__(self):
        """Summarize the EditorialAssignment's basic information."""
        return (
            self.to.user.first_name
            + " "
            + self.to.user.last_name
            + " to become EIC of "
            + self.submission.title[:30]
            + " by "
            + self.submission.author_list[:30]
            + ", requested on "
            + self.date_created.strftime("%Y-%m-%d")
        )

    def get_absolute_url(self):
        """Return the url of the assignment's processing page."""
        return reverse("submissions:pool:assignment_request", args=(self.id,))

    @property
    def preassigned(self):
        return self.status == self.STATUS_PREASSIGNED

    @property
    def invited(self):
        return self.status == self.STATUS_INVITED

    @property
    def replaced(self):
        return self.status == self.STATUS_REPLACED

    @property
    def accepted(self):
        return self.status == self.STATUS_ACCEPTED

    @property
    def deprecated(self):
        return self.status == self.STATUS_DEPRECATED

    @property
    def completed(self):
        return self.status == self.STATUS_COMPLETED

    def send_invitation(self):
        """Send invitation and update status."""
        if self.status != self.STATUS_PREASSIGNED:
            # Only send if status is appropriate to prevent double sending
            return False

        # Send mail
        DirectMailUtil(
            "eic/assignment_request",
            assignment=self,
        ).send_mail()

        EditorialAssignment.objects.filter(id=self.id).update(
            date_invited=timezone.now(), status=self.STATUS_INVITED
        )

        return True


class BaseAssignmentCondition(abc.ABC):
    """
    Base class for conditions that can be attached to ConditionalAssignments.
    """

    @abc.abstractmethod
    def is_met(self, offer: "ConditionalAssignmentOffer") -> bool:
        """
        Check if the condition is met for the given offer.
        """
        raise NotImplementedError

    def accept(self, offer: "ConditionalAssignmentOffer"):
        """
        Accept the offer, potentially modifying the submission in the process.
        """
        offer.submission.add_event_for_eic(
            "Offer by " + str(offer.offered_by) + " accepted: " + str(self)
        )
        offer.submission.add_event_for_author(
            "Accepted offer with condition: " + str(self)
        )


class JournalTransferCondition(BaseAssignmentCondition):
    """
    Condition that offers assignment if the submission is transferred to a different journal.

    Needs to specify the alternative journal in the condition_details
    - `alternative_journal_id`: the journal to which the submission should be transferred.
    """

    def __init__(self, alternative_journal_id: int):
        self.alternative_journal_id = alternative_journal_id

    def __eq__(self, other):
        return (
            isinstance(other, JournalTransferCondition)
            and self.alternative_journal_id == other.alternative_journal_id
        )

    def __hash__(self):
        return hash(self.alternative_journal_id)

    def __str__(self):
        return f"Transfer to {self.alternative_journal}"

    def __repr__(self):
        return str(self)

    @cached_property
    def alternative_journal(self) -> Journal | None:
        try:
            return Journal.objects.get(id=self.alternative_journal_id)
        except Journal.DoesNotExist:
            return None

    def is_met(self, offer: "ConditionalAssignmentOffer") -> bool:
        """
        Check if the submission is transferred to the alternative journal.
        """
        return offer.submission.submitted_to == self.alternative_journal

    def accept(self, offer: "ConditionalAssignmentOffer"):
        """
        Accept the offer, transferring the submission to the alternative journal.
        Also clears out any fulfilled expectations on the submission, as these may no longer be valid.
        """
        if self.alternative_journal is None:
            raise ValueError("The journal for this transfer is not found.")

        if (
            self.alternative_journal
            not in offer.submission.submitted_to.alternative_journals.all()
        ):
            raise ValueError(
                "The alternative journal is not valid for the current journal."
            )

        offer.submission.submitted_to = self.alternative_journal
        offer.submission.fulfilled_expectations = ""
        offer.submission.save()

        super().accept(offer)


class ConditionalAssignmentOffer(models.Model):
    """
    Represents an EditorialAssignment that is offered conditionally.

    Valid condition_type strings are the class names of the subclasses of AssignmentCondition.
    """

    STATUS_OFFERED = "offered"
    STATUS_ACCEPTED = "accepted"
    STATUS_DECLINED = "declined"
    STATUS_FULFILLED = "fulfilled"
    STATUS_CHOICES = (
        (STATUS_OFFERED, "Offered"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_DECLINED, "Declined"),
        (STATUS_FULFILLED, "Fulfilled"),
    )

    CONDITION_CHOICES = [
        (condition, space_uppercase(condition))
        for condition in [
            cls.__name__.replace("Condition", "")
            for cls in BaseAssignmentCondition.__subclasses__()
        ]
    ]

    submission = models.ForeignKey["Submission"](
        "submissions.Submission",
        on_delete=models.CASCADE,
    )
    offered_by = models.ForeignKey["Contributor"](
        "scipost.Contributor",
        on_delete=models.CASCADE,
        related_name="conditional_assignments_offered",
    )
    offered_on = models.DateTimeField(auto_now_add=True, editable=False)
    offered_until = models.DateTimeField(blank=True, null=True)

    accepted_by = models.ForeignKey["Contributor"](
        "scipost.Contributor",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="conditional_assignments_accepted",
    )
    accepted_on = models.DateTimeField(blank=True, null=True)

    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_OFFERED,
    )

    condition_type = models.CharField(
        max_length=32,
        choices=CONDITION_CHOICES,
    )
    condition_details = models.JSONField(default=dict)

    objects = ConditionalAssignmentOfferQuerySet.as_manager()

    class Meta:
        default_related_name = "conditional_assignment_offers"
        ordering = ["-offered_on"]
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "offered_by", "condition_type"],
                name="unique_offer_type_per_submission_fellow",
            )
        ]

    @cached_property
    def condition(self) -> BaseAssignmentCondition:
        """
        Return the condition object for this offer.
        """
        try:
            condition_class = globals()[self.condition_type + "Condition"]
        except KeyError:
            raise ValueError(f"Unknown condition type: {self.condition_type}")

        return condition_class(**self.condition_details)

    def accept(self, by: "Contributor | None"):
        """
        Accept the offer, potentially modifying the submission in the process.
        """
        if self.offered_until and timezone.now() > self.offered_until:
            raise ValueError("The offer has expired.")

        if by is None:
            raise ValueError("The offer must be accepted by a Contributor.")

        if self.status != self.STATUS_OFFERED:
            raise ValueError("The offer has already been processed.")

        if self.submission.editor_in_charge is not None:
            raise ValueError("The submission already has an editor in charge.")

        self.condition.accept(offer=self)

        self.status = self.STATUS_ACCEPTED
        self.accepted_by = by
        self.accepted_on = timezone.now()
        self.save()

    def finalize(self) -> EditorialAssignment | None:
        """
        Check if all conditions are met. If so:
        - Create the EditorialAssignment
        - Set the submission's editor_in_charge to the offering fellow
        - Invalidate all other offers for this submission

        Returns the created EditorialAssignment or None if the conditions are not met.
        """
        from submissions.models import Submission

        # Check that all conditions are met before finalizing
        if not self.condition.is_met(offer=self):
            return

        assignment = EditorialAssignment.objects.create(
            submission=self.submission,
            to=self.offered_by,
            status=EditorialAssignment.STATUS_ACCEPTED,
        )

        Submission.objects.filter(id=self.submission.id).update(
            refereeing_cycle=CYCLE_DEFAULT,
            status=Submission.IN_REFEREEING,
            editor_in_charge=self.offered_by,
            reporting_deadline=None,
            assignment_deadline=None,
            open_for_reporting=True,
            open_for_commenting=True,
            visible_public=True,
            latest_activity=timezone.now(),
        )

        # Invalidate all other offers for this submission
        self.submission.conditional_assignment_offers.exclude(id=self.id).update(
            status=self.STATUS_DECLINED
        )
        self.status = self.STATUS_FULFILLED
        self.save()

        return assignment

    def __str__(self):
        return f"{self.offered_by} to be assigned for {self.submission} with condition: {self.condition}"
