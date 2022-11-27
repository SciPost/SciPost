__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db import models
from django.utils import timezone

from .. import constants


class SubmissionQuerySet(models.QuerySet):

    ##################################
    # Shortcuts for status filtering #
    ##################################
    def incoming(self):
        return self.filter(status=self.model.INCOMING)

    def admission_failed(self):
        return self.filter(status=self.model.ADMISSION_FAILED)

    def prescreening(self):
        return self.filter(status=self.model.PRESCREENING)

    def prescreening_failed(self):
        return self.filter(status=self.model.PRESCREENING_FAILED)

    def screening(self):
        return self.filter(status=self.model.SCREENING)

    def screening_failed(self):
        return self.filter(status=self.model.SCREENING_FAILED)

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

    #### Managers mixing statuses ####

    def under_consideration(self):
        return self.filter(status__in=self.model.UNDER_CONSIDERATION)

    def accepted(self):
        return self.filter(status__in=[
            self.model.ACCEPTED_IN_TARGET,
            self.model.ACCEPTED_IN_ALTERNATIVE,
        ])
    ######################################
    # End shortcuts for status filtering #
    ######################################


    def latest(self):
        return self.exclude(status=self.model.RESUBMITTED)

    def remove_COI(self, user):
        """
        Filter on basic conflicts of interest.

        Prevent conflicts of interest by filtering out submissions
        which are possibly related to user.
        """
        try:
            return self.exclude(authors=user.contributor).exclude(
                models.Q(author_list__icontains=user.last_name), # TODO: replace by Profiles-based checks
                ~models.Q(authors_false_claims=user.contributor),
            )
        except AttributeError:
            return self.none()

    def in_pool(self, user, latest: bool=True, historical: bool=False):
        """
        Filter for Submissions (current or historical) in user's pool.

        If `historical==False`: only submissions UNDER_CONSIDERATION,
        otherwise show full history.

        For non-EdAdmin: user must have active Fellowship and
        be listed in Submission's Fellowship.

        For Senior Fellows, exclude INCOMING status;
        for other Fellows, also exclude PRESCREENING.

        Finally, filter out the COI.
        """
        if not (hasattr(user, "contributor") and
                user.has_perm("scipost.can_view_pool")):
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

        # Fellows can't see incoming and (non-Senior) prescreening
        if user.contributor.is_active_senior_fellow:
            qs = qs.exclude(status__in=[self.model.INCOMING,])
        elif user.contributor.is_active_fellow:
            qs = qs.exclude(status__in=[self.model.INCOMING, self.model.PRESCREENING])

        return qs.remove_COI(user)


    def in_pool_filter_for_eic(self, user, historical: bool=False):
        """Return the set of Submissions the user is Editor-in-charge for.

        If user is an Editorial Administrator: keep any EiC.
        """
        qs = self.in_pool(user, historical)
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
            status__in=[self.model.INCOMING, self.model.SCREENING]
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

    def treated(self):
        """This query returns all Submissions that are presumed to be 'done'."""
        return self.filter(
            status__in=[
                self.model.ACCEPTED,
                self.model.REJECTED,
                self.model.PUBLISHED,
                self.model.RESUBMITTED,
            ]
        )

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

    def awaiting_puboffer_acceptance(self):
        """Return Submissions for which an outstanding publication offer exists."""
        return self.filter(
            status=self.model.ACCEPTED_AWAITING_PUBOFFER_ACCEPTANCE
        )

    def revision_requested(self):
        """Return Submissions with a fixed EICRecommendation: minor or major revision."""
        return self.filter(
            eicrecommendations__status=constants.DECISION_FIXED,
            eicrecommendations__recommendation__in=[
                constants.REPORT_MINOR_REV,
                constants.REPORT_MAJOR_REV,
            ],
        )

    def unpublished(self):
        """Return unpublished Submissions."""
        return self.exclude(status=self.model.PUBLISHED)

    def assignment_failed(self):
        """Return Submissions which have failed assignment."""
        return self.filter(status=self.model.ASSIGNMENT_FAILED)

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
        """Return Submissions that have EditorialAssignments that still need to be sent."""
        return self.filter(editorial_assignments__status=constants.STATUS_PREASSIGNED)

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

    # CLEANUP 2022-11-27
    # def voting_in_preparation(self):
    #     from submissions.models import EICRecommendation

    #     ids_list = [
    #         r.submission.id for r in EICRecommendation.objects.voting_in_preparation()
    #     ]
    #     return self.filter(id__in=ids_list)

    def undergoing_voting(self, longer_than_days=None):
        from submissions.models import EICRecommendation

        ids_list = [
            r.submission.id
            for r in EICRecommendation.objects.put_to_voting(longer_than_days)
        ]
        return self.filter(id__in=ids_list)


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

    def plagiarism_report_to_be_uploaded(self):
        """Return Submissions that has not been sent to iThenticate for their plagiarism check."""
        return self.filter(
            models.Q(plagiarism_report__isnull=True)
            | models.Q(plagiarism_report__status=constants.STATUS_WAITING)
        ).distinct()

    def plagiarism_report_to_be_updated(self):
        """Return Submissions for which their iThenticateReport has not received a report yet."""
        return self.filter(plagiarism_report__status=constants.STATUS_SENT)
