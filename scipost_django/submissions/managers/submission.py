__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db import models
from django.utils import timezone

from .. import constants


class SubmissionQuerySet(models.QuerySet):
    def _newest_version_only(self, queryset):
        """
        TODO: Make more efficient... with agregation or whatever.

        The current Queryset should return only the latest version
        of the submissions.

        Method only compatible with PostgreSQL
        """
        # This method used a double query, which is a consequence of the complex distinct()
        # filter combined with the PostGresQL engine. Without the double query, ordering
        # on a specific field after filtering seems impossible.
        ids = (queryset
               .order_by('thread_hash', '-submission_date')
               .distinct('thread_hash')
               .values_list('id', flat=True))
        return queryset.filter(id__in=ids)

    def user_filter(self, user):
        """Filter on basic conflict of interests.

        Prevent conflict of interest by filtering submissions possibly related to user.
        This filter should be inherited by other filters.
        """
        try:
            return (self.exclude(authors=user.contributor)
                    .exclude(models.Q(author_list__icontains=user.last_name),
                             ~models.Q(authors_false_claims=user.contributor)))
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
        if not hasattr(user, 'contributor'):
            return self.none()

        if user.has_perm('scipost.can_oversee_refereeing'):
            # Editorial Administators do have permission to see all submissions
            # without being one of the College Fellows. Therefore, use the 'old' author
            # filter to still filter out their conflicts of interests.
            return self.user_filter(user)
        else:
            qs = user.contributor.fellowships.active()
            return self.filter(fellows__in=qs)

    def pool(self, user):
        """Return the user-dependent pool of Submissions in active referee phase."""
        allowed_statuses = [
            constants.STATUS_UNASSIGNED,
            constants.STATUS_EIC_ASSIGNED,
            constants.STATUS_ACCEPTED,
            constants.STATUS_ACCEPTED_AWAITING_PUBOFFER_ACCEPTANCE
        ]
        if user.has_perm('scipost.can_oversee_refereeing'):
            allowed_statuses.append(constants.STATUS_INCOMING)
        return self.pool_editable(user).filter(is_current=True, status__in=allowed_statuses)

    def pool_editable(self, user):
        """Return the editable pool for a certain user.

        This is similar to the regular pool, however it also contains submissions that are
        hidden in the regular pool, but should still be able to be opened by for example
        the Editor-in-charge.
        """
        return self._pool(user)

    def filter_for_eic(self, user):
        """Return the set of Submissions the user is Editor-in-charge for.

        If user is an Editorial Administrator: return the full pool.
        """
        qs = self._pool(user)

        if not user.has_perm('scipost.can_oversee_refereeing'):
            qs = qs.filter(editor_in_charge__user=user)
        return qs

    def filter_for_author(self, user):
        """Return the set of Submissions for which the user is a registered author."""
        if not hasattr(user, 'contributor'):
            return self.none()
        return self.filter(authors=user.contributor)

    def prescreening(self):
        """Return submissions just coming in and going through pre-screening."""
        return self.filter(status=constants.STATUS_INCOMING)

    def assigned(self):
        """Return submissions with assigned Editor-in-charge."""
        return self.filter(editor_in_charge__isnull=False)

    def unassigned(self):
        """Return submissions passed pre-screening, but unassigned."""
        return self.filter(status=constants.STATUS_UNASSIGNED)

    def without_eic(self):
        """Return Submissions that still need Editorial Assignment."""
        return self.filter(status__in=[constants.STATUS_INCOMING, constants.STATUS_UNASSIGNED])

    def actively_refereeing(self):
        from ..models import EditorialDecision
        """Return submission currently in some point of the refereeing round."""
        return self.filter(status=constants.STATUS_EIC_ASSIGNED).exclude(
            models.Q(eicrecommendations__status=constants.DECISION_FIXED) &
            ~models.Q(editorialdecision__decision=EditorialDecision.FIXED_AND_ACCEPTED))

    def public(self):
        """Return all publicly available Submissions."""
        return self.filter(visible_public=True)

    def public_listed(self):
        """List all public Submissions if not published and submitted.

        Implement: Use this filter to also determine, using a optional user argument,
                   if the query should be filtered or not as a logged in EdCol Admin
                   should be able to view *all* submissions.
        """
        return self.filter(visible_public=True).exclude(status__in=[
            constants.STATUS_RESUBMITTED,
            constants.STATUS_PUBLISHED])

    def public_newest(self):
        """
        This query contains set of public() submissions, filtered to only the newest available
        version.
        """
        return self._newest_version_only(self.public())

    def treated(self):
        """This query returns all Submissions that are presumed to be 'done'."""
        return self.filter(status__in=[
            constants.STATUS_ACCEPTED,
            constants.STATUS_REJECTED,
            constants.STATUS_PUBLISHED,
            constants.STATUS_RESUBMITTED])

    def originally_submitted(self, from_date, until_date):
        """
        Returns the submissions originally received between from_date and until_date
        (including subsequent resubmissions, even if those came in later).
        """
        thread_hashes = []
        for sub in self.filter(is_resubmission_of__isnull=True,
                               submission_date__range=(from_date, until_date)):
            thread_hashes.append(sub.thread_hash)
        return self.filter(thread_hash__in=thread_hashes)

    def accepted(self):
        """Return accepted Submissions."""
        return self.filter(status=constants.STATUS_ACCEPTED)

    def awaiting_puboffer_acceptance(self):
        """Return Submissions for which an outstanding publication offer exists."""
        return self.filter(status=constants.STATUS_ACCEPTED_AWAITING_PUBOFFER_ACCEPTANCE)

    def revision_requested(self):
        """Return Submissions with a fixed EICRecommendation: minor or major revision."""
        return self.filter(
            eicrecommendations__status=constants.DECISION_FIXED,
            eicrecommendations__recommendation__in=[
                constants.REPORT_MINOR_REV, constants.REPORT_MAJOR_REV])

    def published(self):
        """Return published Submissions."""
        return self.filter(status=constants.STATUS_PUBLISHED)

    def unpublished(self):
        """Return unpublished Submissions."""
        return self.exclude(status=constants.STATUS_PUBLISHED)

    def assignment_failed(self):
        """Return Submissions which have failed assignment."""
        return self.filter(status=constants.STATUS_ASSIGNMENT_FAILED)

    def rejected(self):
        """Return rejected Submissions."""
        return self._newest_version_only(self.filter(status=constants.STATUS_REJECTED))

    def withdrawn(self):
        """Return withdrawn Submissions."""
        return self._newest_version_only(self.filter(status=constants.STATUS_WITHDRAWN))

    def open_for_reporting(self):
        """Return Submission that allow for reporting."""
        return self.filter(open_for_reporting=True)

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
        if not hasattr(user, 'contributor'):
            return self.none()

        return self.filter(is_current=True, status__in=[
            constants.STATUS_INCOMING, constants.STATUS_UNASSIGNED, constants.STATUS_EIC_ASSIGNED,
            ], authors=user.contributor)

    def voting_in_preparation(self):
        from submissions.models import EICRecommendation
        ids_list = [r.submission.id for r in EICRecommendation.objects.voting_in_preparation()]
        return self.filter(id__in=ids_list)

    def undergoing_voting(self):
        from submissions.models import EICRecommendation
        ids_list = [r.submission.id for r in EICRecommendation.objects.put_to_voting()]
        return self.filter(id__in=ids_list)

class SubmissionEventQuerySet(models.QuerySet):
    def for_author(self):
        """Return all events that are meant to be for the author(s) of a submission."""
        return self.filter(event__in=[constants.EVENT_FOR_AUTHOR, constants.EVENT_GENERAL])

    def for_eic(self):
        """Return all events that are meant to be for the Editor-in-charge of a submission."""
        return self.filter(event__in=[constants.EVENT_FOR_EIC, constants.EVENT_GENERAL])

    def last_hours(self, hours=24):
        """Return all events of the last `hours` hours."""
        return self.filter(created__gte=timezone.now() - datetime.timedelta(hours=hours))

    def plagiarism_report_to_be_uploaded(self):
        """Return Submissions that has not been sent to iThenticate for their plagiarism check."""
        return self.filter(
            models.Q(plagiarism_report__isnull=True) |
            models.Q(plagiarism_report__status=constants.STATUS_WAITING)).distinct()

    def plagiarism_report_to_be_updated(self):
        """Return Submissions for which their iThenticateReport has not received a report yet."""
        return self.filter(plagiarism_report__status=constants.STATUS_SENT)
