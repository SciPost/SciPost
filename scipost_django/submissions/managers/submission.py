__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db import models
from django.utils import timezone

from .. import constants


class SubmissionQuerySet(models.QuerySet):

    def latest(self, queryset):
        return queryset.exclude(status=self.model.RESUBMITTED)

    def remove_COI(self, user):
        """
        Filter on basic conflicts of interest.

        Prevent conflicts of interest by filtering submissions possibly related to user.
        This filter should be inherited by other filters.
        """
        try:
            return self.exclude(authors=user.contributor).exclude(
                models.Q(author_list__icontains=user.last_name), # TODO: replace by Profiles-based checks
                ~models.Q(authors_false_claims=user.contributor),
            )
        except AttributeError:
            return self.none()

    def _pool(self, user):
        """Return the user-dependent pool of Submissions.

        This filter creates 'the complete pool' for a user. This new-style pool does
        explicitly not have the author filter anymore, but registered pools for every Submission.

        !!!  IMPORTANT SECURITY NOTICE  !!!
        All permissions regarding Editorial College actions are implicitly taken care
        of in this filter method! ALWAYS use this filter method in your Editorial College
        related view/action.
        """
        if not hasattr(user, "contributor"):
            return self.none()

        if user.has_perm("scipost.can_oversee_refereeing"):
            # Editorial Administators do have permission to see all submissions
            # without being one of the College Fellows. Therefore, use the 'old' author
            # filter to still filter out their conflicts of interests.
            return self.remove_COI(user)
        else:
            qs = user.contributor.fellowships.active()
            return self.filter(fellows__in=qs)

    def pool_for_user(self, user, historical: bool=False):
        """
        Return the pool of Submissions (current or historical), filtered for the user.

        * if user is EdAdmin:

          * `historical==False`: Submission status in UNDER_CONSIDERATION
          * `historical==True`: all

        * if user is currently active Fellow:

          * Fellow in Submission's fellowship and
          * Submission status in UNDER_CONSIDERATION but not INCOMING or PRESCREENING

          * `historical==False`:
          * `historical=True`:

        and then filter for COI.
        """
        # allowed_statuses = [
        #     self.model.UNASSIGNED,
        #     self.model.EIC_ASSIGNED,
        #     self.model.ACCEPTED,
        #     self.model.ACCEPTED_AWAITING_PUBOFFER_ACCEPTANCE,
        # ]
        # if (
        #     user.has_perm("scipost.can_oversee_refereeing")
        #     or user.contributor.is_active_senior_fellow
        # ):
        #     allowed_statuses.append(self.model.INCOMING)
        # return self._pool(user).filter(
        #     is_current=True, status__in=allowed_statuses
        # )
        if not hasattr(user, "contributor"):
            return self.none()

        qs = self.none()
        if user.contributor.is_ed_admin:
            qs = self.filter(status__in=self.model.UNDER_CONSIDERATION)
        else:
            f_ids = user.contributor.fellowships.active()
            qs = self.filter(fellows__in=f_ids)

        if not historical:
            qs = qs.latest()

        return qs.remove_COI(user)


    def filter_for_eic(self, user):
        """Return the set of Submissions the user is Editor-in-charge for.

        If user is an Editorial Administrator: return the full pool.
        """
        qs = self._pool(user)
        if user.is_authenticated and not user.has_perm("scipost.can_oversee_refereeing"):
            qs = qs.filter(editor_in_charge__user=user)
        return qs

    def filter_for_author(self, user):
        """Return the set of Submissions for which the user is a registered author."""
        if not hasattr(user, "contributor"):
            return self.none()
        return self.filter(authors=user.contributor)

    def prescreening(self):
        """Return submissions just coming in and going through pre-screening."""
        return self.filter(status=self.model.INCOMING)

    def assigned(self):
        """Return submissions with assigned Editor-in-charge."""
        return self.filter(editor_in_charge__isnull=False)

    def unassigned(self):
        """Return submissions passed pre-screening, but unassigned."""
        return self.filter(status=self.model.UNASSIGNED)

    def without_eic(self):
        """Return Submissions that still need Editorial Assignment."""
        return self.filter(
            status__in=[self.model.INCOMING, self.model.UNASSIGNED]
        )

    def actively_refereeing(self):
        from ..models import EditorialDecision

        """Return submission currently in some point of the refereeing round."""
        return self.filter(status=self.model.EIC_ASSIGNED).exclude(
            models.Q(eicrecommendations__status=constants.DECISION_FIXED)
            & ~models.Q(
                editorialdecision__decision=EditorialDecision.FIXED_AND_ACCEPTED
            )
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
        return self.latest(self.public())

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

    def accepted(self):
        """Return accepted Submissions."""
        return self.filter(status=self.model.ACCEPTED)

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

    def published(self):
        """Return published Submissions."""
        return self.filter(status=self.model.PUBLISHED)

    def unpublished(self):
        """Return unpublished Submissions."""
        return self.exclude(status=self.model.PUBLISHED)

    def assignment_failed(self):
        """Return Submissions which have failed assignment."""
        return self.filter(status=self.model.ASSIGNMENT_FAILED)

    def rejected(self):
        """Return rejected Submissions."""
        return self.latest(self.filter(status=self.model.REJECTED))

    def withdrawn(self):
        """Return withdrawn Submissions."""
        return self.latest(self.filter(status=self.model.WITHDRAWN))

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
            # is_current=True,
            # status__in=[
            #     self.model.INCOMING,
            #     self.model.UNASSIGNED,
            #     self.model.EIC_ASSIGNED,
            # ],
            status=self.model.AWAITING_RESUBMISSION,
            authors=user.contributor,
        )

    def voting_in_preparation(self):
        from submissions.models import EICRecommendation

        ids_list = [
            r.submission.id for r in EICRecommendation.objects.voting_in_preparation()
        ]
        return self.filter(id__in=ids_list)

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
