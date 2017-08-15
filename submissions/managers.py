import datetime

from django.db import models
from django.db.models import Q
from django.utils import timezone

from .constants import SUBMISSION_STATUS_OUT_OF_POOL, SUBMISSION_STATUS_PUBLICLY_UNLISTED,\
                       SUBMISSION_STATUS_PUBLICLY_INVISIBLE, STATUS_UNVETTED, STATUS_VETTED,\
                       STATUS_UNCLEAR, STATUS_INCORRECT, STATUS_NOT_USEFUL, STATUS_NOT_ACADEMIC,\
                       SUBMISSION_HTTP404_ON_EDITORIAL_PAGE, STATUS_DRAFT, STATUS_PUBLISHED,\
                       SUBMISSION_EXCLUDE_FROM_REPORTING, STATUS_REJECTED_VISIBLE,\
                       STATUS_ACCEPTED, STATUS_RESUBMITTED, STATUS_RESUBMITTED_REJECTED_VISIBLE,\
                       EVENT_FOR_EIC, EVENT_GENERAL, EVENT_FOR_AUTHOR, STATUS_UNASSIGNED


class SubmissionQuerySet(models.QuerySet):
    def _newest_version_only(self, queryset):
        """
        The current Queryset should return only the latest version
        of the Arxiv submissions known to SciPost.

        Method only compatible with PostGresQL
        """
        # This method used a double query, which is a consequence of the complex distinct()
        # filter combined with the PostGresQL engine. Without the double query, ordering
        # on a specific field after filtering would be impossible.
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

    def get_pool(self, user):
        """
        Return subset of active and newest 'alive' submissions.
        """
        return (self.user_filter(user)
                .exclude(is_current=False)
                .exclude(status__in=SUBMISSION_STATUS_OUT_OF_POOL)
                .order_by('-submission_date'))

    def filter_editorial_page(self, user):
        """
        Return Submissions currently 'alive' (being refereed, not published).

        It is meant to allow opening and editing certain submissions that are officially
        out of the submission cycle i.e. due to resubmission, but should still have the
        possibility to be opened by the EIC.
        """
        return (self.user_filter(user)
                .exclude(status__in=SUBMISSION_HTTP404_ON_EDITORIAL_PAGE)
                .order_by('-submission_date'))

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
                    .exclude(status__in=[STATUS_UNASSIGNED, STATUS_ACCEPTED]))

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

    def accepted(self):
        return self.filter(status=STATUS_ACCEPTED)

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
        return self.filter(completed=False).accepted()


class EICRecommendationManager(models.Manager):
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
        Return list of EICRecommendation's which are owned/assigned author through the
        related submission.
        """
        try:
            return self.filter(submission__authors=user.contributor).filter(**kwargs)
        except AttributeError:
            return self.none()


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
    def pending(self):
        return self.filter(accepted=None)

    def accepted(self):
        return self.filter(accepted=True)

    def declined(self):
        return self.filter(accepted=False)
