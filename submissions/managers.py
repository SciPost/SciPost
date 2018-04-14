__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db import models
from django.db.models import Q
from django.utils import timezone

from .constants import SUBMISSION_STATUS_OUT_OF_POOL, SUBMISSION_STATUS_PUBLICLY_UNLISTED,\
                       SUBMISSION_STATUS_PUBLICLY_INVISIBLE, STATUS_UNVETTED, STATUS_VETTED,\
                       STATUS_UNCLEAR, STATUS_INCORRECT, STATUS_NOT_USEFUL, STATUS_NOT_ACADEMIC,\
                       SUBMISSION_HTTP404_ON_EDITORIAL_PAGE, STATUS_DRAFT, STATUS_PUBLISHED,\
                       SUBMISSION_EXCLUDE_FROM_REPORTING,\
                       STATUS_REJECTED, STATUS_REJECTED_VISIBLE,\
                       STATUS_ACCEPTED, STATUS_RESUBMITTED, STATUS_RESUBMITTED_REJECTED_VISIBLE,\
                       EVENT_FOR_EIC, EVENT_GENERAL, EVENT_FOR_AUTHOR,\
                       STATUS_UNASSIGNED, STATUS_ASSIGNMENT_FAILED, STATUS_WITHDRAWN,\
                       STATUS_PUT_TO_EC_VOTING, STATUS_VOTING_IN_PREPARATION,\
                       SUBMISSION_STATUS_VOTING_DEPRECATED, STATUS_REVISION_REQUESTED

now = timezone.now()


class SubmissionQuerySet(models.QuerySet):
    def _newest_version_only(self, queryset):
        """
        The current Queryset should return only the latest version
        of the Arxiv submissions known to SciPost.

        Method only compatible with PostGresQL
        """
        # This method used a double query, which is a consequence of the complex distinct()
        # filter combined with the PostGresQL engine. Without the double query, ordering
        # on a specific field after filtering seems impossible.
        ids = (queryset
               .order_by('arxiv_identifier_wo_vn_nr', '-arxiv_vn_nr')
               .distinct('arxiv_identifier_wo_vn_nr')
               .values_list('id', flat=True))
        return queryset.filter(id__in=ids)

    def user_filter(self, user):
        """
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
        """
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
        """Return the pool for a certain user: filtered to "in active referee phase"."""
        qs = self._pool(user)
        qs = qs.exclude(is_current=False).exclude(status__in=SUBMISSION_STATUS_OUT_OF_POOL)
        return qs

    def pool_editable(self, user):
        """Return the editable pool for a certain user.

        This is similar to the regular pool, however it also contains submissions that are
        hidden in the regular pool, but should still be able to be opened by for example
        the Editor-in-charge.
        """
        qs = self._pool(user)
        qs = qs.exclude(status__in=SUBMISSION_HTTP404_ON_EDITORIAL_PAGE)
        return qs

    def pool_full(self, user):
        """
        Return the *FULL* pool for a certain user.
        This makes sure the user can see all history of Submissions related to its Fellowship(s).

        Do not use this filter by default however, as this also contains Submissions
        that are for example either rejected or accepted already and thus "inactive."
        """
        qs = self._pool(user)
        return qs

    def filter_for_eic(self, user):
        """
        Return the set of Submissions the user is Editor-in-charge for or return the pool if
        User is Editorial Administrator.
        """
        qs = self._pool(user)

        if not user.has_perm('scipost.can_oversee_refereeing') and hasattr(user, 'contributor'):
            qs = qs.filter(editor_in_charge=user.contributor)
        return qs

    def filter_for_author(self, user):
        """
        Return the set of Submissions for which the user is a registered author.
        """
        if not hasattr(user, 'contributor'):
            return self.none()
        return self.filter(authors=user.contributor)

    def prescreening(self):
        """
        Return submissions just coming in and going through pre-screening.
        """
        return self.filter(status=STATUS_UNASSIGNED)

    def actively_refereeing(self):
        """
        Return submission currently in some point of the refereeing round.
        """
        return (self.exclude(is_current=False)
                    .exclude(status__in=SUBMISSION_STATUS_OUT_OF_POOL)
                    .exclude(status__in=[STATUS_UNASSIGNED, STATUS_ACCEPTED,
                                         STATUS_REVISION_REQUESTED]))

    def public(self):
        """
        This query contains set of public submissions, i.e. also containing
        submissions with status "published" or "resubmitted".
        """
        return self.exclude(status__in=SUBMISSION_STATUS_PUBLICLY_INVISIBLE)

    def public_unlisted(self):
        """
        List only all public submissions. Should be used as a default filter!

        Implement: Use this filter to also determine, using a optional user argument,
                   if the query should be filtered or not as a logged in EdCol Admin
                   should be able to view *all* submissions.
        """
        return self.exclude(status__in=SUBMISSION_STATUS_PUBLICLY_UNLISTED)

    def public_newest(self):
        """
        This query contains set of public() submissions, filtered to only the newest available
        version.
        """
        return self._newest_version_only(self.public())

    def treated(self):
        """
        This query returns all Submissions that are expected to be 'done'.
        """
        return self.filter(status__in=[STATUS_ACCEPTED, STATUS_REJECTED_VISIBLE, STATUS_PUBLISHED,
                                       STATUS_RESUBMITTED, STATUS_RESUBMITTED_REJECTED_VISIBLE])

    def originally_submitted(self, from_date, until_date):
        """
        Returns the submissions originally received between from_date and until_date
        (including subsequent resubmissions, even if those came in later).
        """
        identifiers = []
        for sub in self.filter(is_resubmission=False,
                               submission_date__range=(from_date, until_date)):
            identifiers.append(sub.arxiv_identifier_wo_vn_nr)
        return self.filter(arxiv_identifier_wo_vn_nr__in=identifiers)

    def accepted(self):
        return self.filter(status=STATUS_ACCEPTED)

    def revision_requested(self):
        return self.filter(status=STATUS_REVISION_REQUESTED)

    def published(self):
        return self.filter(status=STATUS_PUBLISHED)

    def assignment_failed(self):
        return self.filter(status=STATUS_ASSIGNMENT_FAILED)

    def rejected(self):
        return self._newest_version_only(self.filter(status__in=[STATUS_REJECTED,
                                                                 STATUS_REJECTED_VISIBLE]))

    def withdrawn(self):
        return self._newest_version_only(self.filter(status=STATUS_WITHDRAWN))

    def open_for_reporting(self):
        """
        Return Submissions that have appriopriate status for reporting.
        The `open_for_reporting` property is not filtered as some invited visitors
        still need to have access.
        """
        return self.exclude(status__in=SUBMISSION_EXCLUDE_FROM_REPORTING)

    def open_for_commenting(self):
        """ Return Submission that allow for commenting. """
        return self.filter(open_for_commenting=True)


class SubmissionEventQuerySet(models.QuerySet):
    def for_author(self):
        """
        Return all events that are meant to be for the author(s) of a submission.
        """
        return self.filter(event__in=[EVENT_FOR_AUTHOR, EVENT_GENERAL])

    def for_eic(self):
        """
        Return all events that are meant to be for the Editor-in-charge of a submission.
        """
        return self.filter(event__in=[EVENT_FOR_EIC, EVENT_GENERAL])

    def last_hours(self, hours=24):
        """
        Return all events of the last `hours` hours.
        """
        return self.filter(created__gte=timezone.now() - datetime.timedelta(hours=hours))


class EditorialAssignmentQuerySet(models.QuerySet):
    def get_for_user_in_pool(self, user):
        return self.exclude(submission__authors=user.contributor)\
                .exclude(Q(submission__author_list__icontains=user.last_name),
                         ~Q(submission__authors_false_claims=user.contributor))

    def last_year(self):
        return self.filter(date_created__gt=timezone.now() - timezone.timedelta(days=365))

    def accepted(self):
        return self.filter(accepted=True)

    def refused(self):
        return self.filter(accepted=False)

    def ignored(self):
        return self.filter(accepted=None)

    def completed(self):
        return self.filter(completed=True)

    def ongoing(self):
        return self.filter(completed=False, deprecated=False).accepted()

    def open(self):
        return self.filter(accepted=None, deprecated=False)

    def refereeing_deadline_within(self, days=7):
        return self.exclude(
            submission__reporting_deadline__gt=timezone.now() + timezone.timedelta(days=days)
            ).exclude(submission__reporting_deadline__lt=timezone.now())


class EICRecommendationQuerySet(models.QuerySet):
    def get_for_user_in_pool(self, user):
        """
        -- DEPRECATED --

        Return list of EICRecommendation which are filtered as these objects
        are not related to the Contributor, by checking last_name and author_list of
        the linked Submission.
        """
        try:
            return self.exclude(submission__authors=user.contributor)\
                       .exclude(Q(submission__author_list__icontains=user.last_name),
                                ~Q(submission__authors_false_claims=user.contributor))
        except AttributeError:
            return self.none()

    def filter_for_user(self, user, **kwargs):
        """
        -- DEPRECATED --

        Return list of EICRecommendation's which are owned/assigned author through the
        related submission.
        """
        try:
            return self.filter(submission__authors=user.contributor).filter(**kwargs)
        except AttributeError:
            return self.none()

    def user_may_vote_on(self, user):
        if not hasattr(user, 'contributor'):
            return self.none()

        return (self.filter(eligible_to_vote=user.contributor)
                .exclude(recommendation__in=[-1, -2])
                .exclude(voted_for=user.contributor)
                .exclude(voted_against=user.contributor)
                .exclude(voted_abstain=user.contributor)
                .exclude(submission__status__in=SUBMISSION_STATUS_VOTING_DEPRECATED))

    def put_to_voting(self):
        return self.filter(submission__status=STATUS_PUT_TO_EC_VOTING)

    def voting_in_preparation(self):
        return self.filter(submission__status=STATUS_VOTING_IN_PREPARATION)

    def active(self):
        return self.filter(active=True)


class ReportQuerySet(models.QuerySet):
    def accepted(self):
        return self.filter(status=STATUS_VETTED)

    def awaiting_vetting(self):
        return self.filter(status=STATUS_UNVETTED)

    def rejected(self):
        return self.filter(status__in=[STATUS_UNCLEAR, STATUS_INCORRECT,
                                       STATUS_NOT_USEFUL, STATUS_NOT_ACADEMIC])

    def in_draft(self):
        return self.filter(status=STATUS_DRAFT)

    def non_draft(self):
        return self.exclude(status=STATUS_DRAFT)

    def contributed(self):
        return self.filter(invited=False)

    def invited(self):
        return self.filter(invited=True)


class RefereeInvitationQuerySet(models.QuerySet):
    def awaiting_response(self):
        return self.pending().open()

    def pending(self):
        return self.filter(accepted=None)

    def accepted(self):
        return self.filter(accepted=True)

    def declined(self):
        return self.filter(accepted=False)

    def open(self):
        return self.pending().filter(cancelled=False)

    def in_process(self):
        return self.accepted().filter(fulfilled=False)

    def approaching_deadline(self):
        qs = self.in_process()
        psuedo_deadline = now + datetime.timedelta(days=2)
        deadline = datetime.datetime.now()
        qs = qs.filter(submission__reporting_deadline__lte=psuedo_deadline,
                       submission__reporting_deadline__gte=deadline)
        return qs

    def overdue(self):
        qs = self.in_process()
        deadline = now
        qs = qs.filter(submission__reporting_deadline__lte=deadline)
        return qs


class EditorialCommunicationQueryset(models.QuerySet):
    def for_referees(self):
        return self.filter(comtype__in=['EtoR', 'RtoE'])
