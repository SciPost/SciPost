__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db import models
from django.utils import timezone

from .. import constants

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...scipost.models import Contributor


class SubmissionQuerySet(models.QuerySet):
    ##################################
    # Shortcuts for status filtering #
    ##################################
    def incoming(self):
        return self.filter(status=self.model.INCOMING)

    def admissible(self):
        return self.filter(status=self.model.ADMISSIBLE)

    def admission_failed(self):
        return self.filter(status=self.model.ADMISSION_FAILED)

    def preassignment(self):
        return self.filter(status=self.model.PREASSIGNMENT)

    def preassignment_failed(self):
        return self.filter(status=self.model.PREASSIGNMENT_FAILED)

    def seeking_assignment(self):
        return self.filter(status=self.model.SEEKING_ASSIGNMENT)

    def assignment_failed(self):
        return self.filter(status=self.model.ASSIGNMENT_FAILED)

    def refereeing_in_preparation(self):
        return self.filter(status=self.model.REFEREEING_IN_PREPARATION)

    def in_refereeing(self):
        return self.filter(status=self.model.IN_REFEREEING)

    def refereeing_closed(self):
        return self.filter(status=self.model.REFEREEING_CLOSED)

    def awaiting_resubmission(self):
        return self.filter(status=self.model.AWAITING_RESUBMISSION)

    def resubmitted(self):
        return self.filter(status=self.model.RESUBMITTED)

    def voting_in_preparation(self):
        return self.filter(status=self.model.VOTING_IN_PREPARATION)

    def in_voting(self):
        return self.filter(status=self.model.IN_VOTING)

    def awaiting_decision(self):
        return self.filter(status=self.model.AWAITING_DECISION)

    def accepted_in_target(self):
        return self.filter(status=self.model.ACCEPTED_IN_TARGET)

    def accepted_in_alternative_awaiting_puboffer_acceptance(self):
        return self.filter(
            status=self.model.ACCEPTED_IN_ALTERNATIVE_AWAITING_PUBOFFER_ACCEPTANCE
        )

    def accepted_in_alternative(self):
        return self.filter(status=self.model.ACCEPTED_IN_ALTERNATIVE)

    def rejected(self):
        return self.latest().filter(status=self.model.REJECTED)

    def withdrawn(self):
        return self.latest().filter(status=self.model.WITHDRAWN)

    def published(self):
        return self.filter(status=self.model.PUBLISHED)

    ### Managers for stages ####

    def in_stage_incoming(self):
        return self.filter(status__in=self.model.STAGE_INCOMING)

    def stage_incoming_completed(self):
        return self.filter(status__in=self.model.STAGE_INCOMING_COMPLETED_STATUSES)

    def in_stage_preassignment(self):
        return self.filter(status__in=self.model.STAGE_PREASSIGNMENT)

    def stage_preassignment_completed(self):
        return self.filter(status__in=self.model.STAGE_PREASSIGNMENT_COMPLETED_STATUSES)

    def in_stage_assignment(self):
        return self.filter(status__in=self.model.STAGE_ASSIGNMENT)

    def stage_assignment_completed(self):
        return self.filter(status__in=self.model.STAGE_ASSIGNMENT_COMPLETED_STATUSES)

    def in_stage_refereeing_in_preparation(self):
        return self.filter(status__in=self.model.STAGE_REFEREEING_IN_PREPARATION)

    def stage_refereeing_in_preparation_completed(self):
        return self.filter(
            status__in=self.model.STAGE_REFEREEING_IN_PREPARATION_COMPLETED_STATUSES
        )

    def in_stage_in_refereeing(self):
        return self.filter(status__in=self.model.STAGE_IN_REFEREEING)

    def stage_in_refereeing_completed(self):
        return self.filter(status__in=self.model.STAGE_IN_REFEREEING_COMPLETED_STATUSES)

    def in_stage_decisionmaking(self):
        return self.filter(status__in=self.model.STAGE_DECISIONMAKING)

    def stage_decisionmaking_completed(self):
        return self.filter(status__in=self.model.STAGE_DECIDED)

    def in_state_in_production(self):
        return self.filter(status__in=self.model.STAGE_IN_PRODUCTION)

    #### Other managers mixing statuses ####

    def under_consideration(self):
        return self.filter(status__in=self.model.UNDER_CONSIDERATION)

    def treated(self):
        """Returns Submissions (stream heads) whose streams are fully processed."""
        return self.filter(status__in=self.model.TREATED)

    def accepted(self):
        return self.filter(
            status__in=[
                self.model.ACCEPTED_IN_TARGET,
                self.model.ACCEPTED_IN_ALTERNATIVE,
            ]
        )

    ######################################
    # End shortcuts for status filtering #
    ######################################

    def latest(self):
        return self.exclude(status=self.model.RESUBMITTED)

    def with_potential_unclaimed_author(self, contributor: "Contributor"):
        """
        Return Submissions for which the contributor could potentially be an author.
        """
        return (
            self.filter(author_list__unaccent__icontains=contributor.user.last_name)
            .exclude(authors=contributor)
            .exclude(authors_claims=contributor)
            .exclude(authors_false_claims=contributor)
        )

    def remove_COI(self, contributor: "Contributor"):
        """
        Filter on basic conflicts of interest.

        Prevent conflicts of interest by filtering out submissions
        which are possibly related to user.
        """
        return self.exclude(authors=contributor).exclude(
            models.Q(
                author_list__unaccent__icontains=contributor.user.last_name
            ),  # TODO: replace by Profiles-based checks
            ~models.Q(authors_false_claims=contributor),
        )

    def in_pool(self, user, latest: bool = True, historical: bool = False):
        """
        Filter for Submissions (current or historical) in user's pool.

        If `historical==False`: only submissions UNDER_CONSIDERATION,
        otherwise show full history.

        For non-EdAdmin: user must have active Fellowship and
        be listed in Submission's Fellowship.

        For Senior Fellows, exclude INCOMING status;
        for other Fellows, also exclude PREASSIGNMENT.

        Finally, filter out the COI.
        """
        if not (
            hasattr(user, "contributor")
            and (user.contributor.is_ed_admin or user.contributor.is_active_fellow)
        ):
            return self.none()

        qs = self
        if latest:
            qs = qs.latest()
        if not historical:
            qs = qs.filter(status__in=self.model.UNDER_CONSIDERATION)

        # for non-EdAdmin, filter: in Submission's Fellowship
        if not user.contributor.is_ed_admin:
            f_ids = user.contributor.fellowships.active()
            qs = qs.filter(fellows__in=f_ids)

        if user.contributor.is_scipost_admin:
            pass
        # Fellows can't see incoming and (non-Senior) preassignment
        elif user.contributor.is_active_senior_fellow:
            qs = qs.exclude(
                status__in=[
                    self.model.INCOMING,
                ]
            )
        elif user.contributor.is_active_fellow:
            qs = qs.exclude(status__in=[self.model.INCOMING, self.model.PREASSIGNMENT])

        # remove Submissions for which a competing interest exists:
        qs = qs.exclude(
            competing_interests__profile=user.contributor.profile,
        ).exclude(
            competing_interests__related_profile=user.contributor.profile,
        )
        return qs.remove_COI(user.contributor)

    def in_pool_filter_for_eic(
        self,
        user,
        latest: bool = True,
        historical: bool = False,
    ):
        """Return the set of Submissions the user is Editor-in-charge for.

        If user is an Editorial Administrator: keep any EiC.
        """
        qs = self.in_pool(user, latest=latest, historical=historical)
        if user.is_authenticated and not user.contributor.is_ed_admin:
            qs = qs.filter(editor_in_charge__user=user)
        return qs

    def filter_for_author(self, user):
        """Return the set of Submissions for which the user is a registered author."""
        if not hasattr(user, "contributor"):
            return self.none()
        return self.filter(authors=user.contributor)

    def assigned(self):
        """Return submissions with assigned Editor-in-charge."""
        return self.filter(editor_in_charge__isnull=False)

    def without_eic(self):
        """Return Submissions that still need Editorial Assignment."""
        return self.filter(
            status__in=[self.model.PREASSIGNMENT, self.model.SEEKING_ASSIGNMENT]
        )

    def public(self):
        """Return all publicly available Submissions."""
        return self.filter(visible_public=True)

    def public_listed(self):
        """List all public Submissions if not published and submitted.

        Implement: Use this filter to also determine, using a optional user argument,
                   if the query should be filtered or not as a logged in EdCol Admin
                   should be able to view *all* submissions.
        """
        return self.filter(visible_public=True).exclude(
            status__in=[self.model.RESUBMITTED, self.model.PUBLISHED]
        )

    def public_latest(self):
        """
        This query contains set of public() submissions, filtered to only the latest available
        version.
        """
        return self.latest().public()

    def originally_submitted(self, from_date, until_date):
        """
        Returns the submissions originally received between from_date and until_date
        (including subsequent resubmissions, even if those came in later).
        """
        thread_hashes = []
        for sub in self.filter(
            is_resubmission_of__isnull=True,
            submission_date__range=(from_date, until_date),
        ):
            thread_hashes.append(sub.thread_hash)
        return self.filter(thread_hash__in=thread_hashes)

    def unpublished(self):
        """Return unpublished Submissions."""
        return self.exclude(status=self.model.PUBLISHED)

    def open_for_reporting(self):
        """Return Submissions open for reporting."""
        return self.filter(open_for_reporting=True)

    def reports_needed(self):
        """
        Return Submissions for which the nr of Reports is less than required by target Journal.
        """
        qs = self.prefetch_related("reports", "submitted_to").annotate(
            nr_reports=models.Count("reports")
        )
        ids_list = [
            s.id
            for s in qs.all()
            if (s.nr_reports < s.submitted_to.minimal_nr_of_reports)
        ]
        return self.filter(id__in=ids_list)

    def open_for_commenting(self):
        """Return Submission that allow for commenting."""
        return self.filter(open_for_commenting=True)

    def needs_conflicts_update(self):
        """Return set of Submissions that need an ConflictOfInterest update."""
        return self.filter(needs_conflicts_update=True)

    def has_editor_invitations_to_be_sent(self):
        from submissions.models import EditorialAssignment

        """Return Submissions that have EditorialAssignments that still need to be sent."""
        return self.filter(
            editorial_assignments__status=EditorialAssignment.STATUS_PREASSIGNED,
        )

    def candidate_for_resubmission(self, user):
        """
        Return all Submissions that are open for resubmission specialised for a certain User.
        """
        if not hasattr(user, "contributor"):
            return self.none()

        return self.filter(
            status__in=[
                self.model.AWAITING_RESUBMISSION,
            ],
            authors=user.contributor,
        )

    def undergoing_voting(self, longer_than_days=None):
        from submissions.models import EICRecommendation

        ids_list = [
            r.submission.id
            for r in EICRecommendation.objects.put_to_voting(longer_than_days)
        ]
        return self.filter(id__in=ids_list)

    def annot_qualified_by(self, fellow):
        """
        Annotate Submissions with a boolean indicating if the fellow has provided a Qualification.
        """
        return self.annotate(
            has_qualification=models.Exists(
                fellow.qualification_set.filter(submission=models.OuterRef("pk"))
            )
        )

    def annot_readiness_by(self, fellow):
        """
        Annotate Submissions with a boolean indicating if the fellow has provided a Readiness.
        """
        return self.annotate(
            has_readiness=models.Exists(
                fellow.readiness_set.filter(submission=models.OuterRef("pk"))
            )
        )

    def annot_clearance_by(self, profile):
        """
        Annotate Submissions with a boolean indicating if the profile has provided a Clearance.
        """
        return self.annotate(
            has_clearance=models.Exists(
                profile.submission_clearances.filter(submission=models.OuterRef("pk"))
            )
        )

    def not_fully_appraised_by(self, fellow):
        """
        Return Submissions that are not fully appraised yet by the fellow,
        i.e. missing Qualification, Readiness or Clearance.
        """
        return (
            self.annot_qualified_by(fellow)
            .annot_readiness_by(fellow)
            .annot_clearance_by(fellow.contributor.profile)
            .exclude(has_qualification=True, has_readiness=True, has_clearance=True)
        )


class SubmissionEventQuerySet(models.QuerySet):
    def for_edadmin(self):
        """Return all events that are visible to EdAdmin."""
        return self.filter(
            event__in=[
                constants.EVENT_FOR_EDADMIN,
                constants.EVENT_FOR_EIC,
                constants.EVENT_GENERAL,
            ]
        )

    def for_eic(self):
        """Return all events that are visible to Editor-in-charge of a submission."""
        return self.filter(event__in=[constants.EVENT_FOR_EIC, constants.EVENT_GENERAL])

    def for_author(self):
        """Return all events that are visible to author(s) of a submission."""
        return self.filter(
            event__in=[constants.EVENT_FOR_AUTHOR, constants.EVENT_GENERAL]
        )

    def last_hours(self, hours=24):
        """Return all events of the last `hours` hours."""
        return self.filter(
            created__gte=timezone.now() - datetime.timedelta(hours=hours)
        )

    def iThenticate_plagiarism_report_to_be_uploaded(self):
        """Return Submissions that has not been sent to iThenticate for their plagiarism check."""
        return self.filter(
            models.Q(iThenticate_plagiarism_report__isnull=True)
            | models.Q(iThenticate_plagiarism_report__status=constants.STATUS_WAITING)
        ).distinct()

    def iThenticate_plagiarism_report_to_be_updated(self):
        """Return Submissions for which their iThenticateReport has not received a report yet."""
        return self.filter(iThenticate_plagiarism_report__status=constants.STATUS_SENT)
