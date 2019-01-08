__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from . import constants

now = timezone.now()


class SubmissionQuerySet(models.QuerySet):
    def _newest_version_only(self, queryset):
        """
        TODO: Make more efficient... with agregation or whatever.

        The current Queryset should return only the latest version
        of the Arxiv submissions known to SciPost.

        Method only compatible with PostGresQL
        """
        # This method used a double query, which is a consequence of the complex distinct()
        # filter combined with the PostGresQL engine. Without the double query, ordering
        # on a specific field after filtering seems impossible.
        ids = (queryset
               .order_by('preprint__identifier_wo_vn_nr', '-preprint__vn_nr')
               .distinct('preprint__identifier_wo_vn_nr')
               .values_list('id', flat=True))
        return queryset.filter(id__in=ids)

    def user_filter(self, user):
        """Filter on basic conflict of interests.

        Prevent conflict of interest by filtering submissions possibly related to user.
        This filter should be inherited by other filters.
        """
        try:
            return (self.exclude(authors=user.contributor)
                    .exclude(Q(author_list__icontains=user.last_name),
                             ~Q(authors_false_claims=user.contributor)))
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
        return self.pool_editable(user).filter(is_current=True, status__in=[
            constants.STATUS_UNASSIGNED,
            constants.STATUS_EIC_ASSIGNED,
            constants.STATUS_ACCEPTED])

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
        """Return submission currently in some point of the refereeing round."""
        return self.filter(status=constants.STATUS_EIC_ASSIGNED).exclude(
            eicrecommendations__status=constants.DECISION_FIXED)

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
        identifiers = []
        for sub in self.filter(is_resubmission_of__isnull=True,
                               submission_date__range=(from_date, until_date)):
            identifiers.append(sub.preprint.identifier_wo_vn_nr)
        return self.filter(preprint__identifier_wo_vn_nr__in=identifiers)

    def accepted(self):
        """Return accepted Submissions."""
        return self.filter(status=constants.STATUS_ACCEPTED)

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


class EditorialAssignmentQuerySet(models.QuerySet):
    def get_for_user_in_pool(self, user):
        return self.exclude(submission__authors=user.contributor).exclude(
            Q(submission__author_list__icontains=user.last_name),
            ~Q(submission__authors_false_claims=user.contributor))

    def auto_reminders_allowed(self):
        return self.filter(auto_reminders_allowed=True)

    def last_year(self):
        return self.filter(date_created__gt=timezone.now() - timezone.timedelta(days=365))

    def refereeing_deadline_within(self, days=7):
        return self.exclude(
            submission__reporting_deadline__gt=timezone.now() + timezone.timedelta(days=days)
            ).exclude(submission__reporting_deadline__lt=timezone.now())

    def next_invitation_to_be_sent(self, submission_id):
        """Return EditorialAssignment that needs to be sent next."""
        try:
            latest_date_invited = self.invited().filter(
                submission__id=submission_id,
                date_invited__isnull=False).latest('date_invited').date_invited
            if latest_date_invited:
                return_next = latest_date_invited < timezone.now() - settings.ED_ASSIGMENT_DT_DELTA
            else:
                return_next = True
        except self.model.DoesNotExist:
            return_next = True

        if not return_next:
            return None

        return self.filter(
            submission__id=submission_id,
            status=constants.STATUS_PREASSIGNED).order_by('invitation_order').first()

    def preassigned(self):
        return self.filter(status=constants.STATUS_PREASSIGNED)

    def invited(self):
        return self.filter(status=constants.STATUS_INVITED)

    def need_response(self):
        """Return EdAssignments that are non-deprecated or without response."""
        return self.filter(status__in=[constants.STATUS_PREASSIGNED, constants.STATUS_INVITED])

    def ongoing(self):
        return self.filter(status=constants.STATUS_ACCEPTED)

    def accepted(self):
        return self.filter(status__in=[constants.STATUS_ACCEPTED, constants.STATUS_COMPLETED])

    def declined(self):
        return self.filter(status=constants.STATUS_DECLINED)

    def declined_red(self):
        """Return EditorialAssignments declined with a 'red-label reason'."""
        return self.declined().filter(refusal_reason__in=['NIE', 'DNP'])

    def deprecated(self):
        return self.filter(status=constants.STATUS_DEPRECATED)

    def completed(self):
        return self.filter(status=constants.STATUS_COMPLETED)


class EICRecommendationQuerySet(models.QuerySet):
    """QuerySet for the EICRecommendation model."""

    def user_must_vote_on(self, user):
        """Return the subset of EICRecommendation the User is requested to vote on."""
        if not hasattr(user, 'contributor'):
            return self.none()

        return self.put_to_voting().filter(eligible_to_vote=user.contributor).exclude(
            recommendation__in=[-1, -2]).exclude(
                models.Q(voted_for=user.contributor) | models.Q(voted_against=user.contributor) |
                models.Q(voted_abstain=user.contributor)).exclude(submission__status__in=[
                    constants.STATUS_REJECTED,
                    constants.STATUS_PUBLISHED,
                    constants.STATUS_WITHDRAWN]).distinct()

    def user_current_voted(self, user):
        """
        Return the subset of EICRecommendations currently undergoing voting, for
        which the User has already voted.
        """
        if not hasattr(user, 'contributor'):
            return self.none()
        return self.put_to_voting().filter(eligible_to_vote=user.contributor).exclude(
            recommendation__in=[-1, -2]).filter(
                models.Q(voted_for=user.contributor) | models.Q(voted_against=user.contributor) |
                models.Q(voted_abstain=user.contributor)).exclude(submission__status__in=[
                    constants.STATUS_REJECTED,
                    constants.STATUS_PUBLISHED,
                    constants.STATUS_WITHDRAWN]).distinct()

    def put_to_voting(self):
        """Return the subset of EICRecommendation currently undergoing voting."""
        return self.filter(status=constants.PUT_TO_VOTING)

    def voting_in_preparation(self):
        """Return the subset of EICRecommendation currently undergoing preparation for voting."""
        return self.filter(status=constants.VOTING_IN_PREP)

    def active(self):
        """Return the subset of EICRecommendation most recent, valid versions."""
        return self.exclude(status=constants.DEPRECATED)

    def fixed(self):
        """Return the subset of fixed EICRecommendations."""
        return self.filter(status=constants.DECISION_FIXED)

    def asking_revision(self):
        """Return EICRecommendation asking for a minor or major revision."""
        return self.filter(recommendation__in=[-1, -2])


class ReportQuerySet(models.QuerySet):
    def accepted(self):
        return self.filter(status=constants.STATUS_VETTED)

    def awaiting_vetting(self):
        return self.filter(status=constants.STATUS_UNVETTED)

    def rejected(self):
        return self.filter(status__in=[
            constants.STATUS_UNCLEAR, constants.STATUS_INCORRECT, constants.STATUS_NOT_USEFUL,
            constants.STATUS_NOT_ACADEMIC])

    def in_draft(self):
        return self.filter(status=constants.STATUS_DRAFT)

    def non_draft(self):
        return self.exclude(status=constants.STATUS_DRAFT)

    def contributed(self):
        return self.filter(invited=False)

    def invited(self):
        return self.filter(invited=True)


class RefereeInvitationQuerySet(models.QuerySet):
    def awaiting_response(self):
        return self.pending().open()

    def pending(self):
        return self.filter(accepted=None, cancelled=False)

    def accepted(self):
        return self.filter(accepted=True, cancelled=False)

    def declined(self):
        return self.filter(accepted=False)

    def open(self):
        return self.pending().filter(cancelled=False)

    def in_process(self):
        return self.accepted().filter(fulfilled=False, cancelled=False)

    def approaching_deadline(self, days=2):
        qs = self.in_process()
        pseudo_deadline = now + datetime.timedelta(days)
        deadline = datetime.datetime.now()
        qs = qs.filter(submission__reporting_deadline__lte=pseudo_deadline,
                       submission__reporting_deadline__gte=deadline)
        return qs

    def overdue(self):
        return self.in_process().filter(submission__reporting_deadline__lte=now)


class EditorialCommunicationQueryset(models.QuerySet):
    def for_referees(self):
        return self.filter(comtype__in=['EtoR', 'RtoE'])
