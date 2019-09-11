__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.utils import timezone

from .constants import STATUS_DRAFT, STATUS_PUBLICLY_OPEN, STATUS_PUBLISHED,\
    PUBLICATION_PUBLISHED,\
    ISSUES_AND_VOLUMES, ISSUES_ONLY, INDIVIDUAL_PUBLICATIONS


class JournalQuerySet(models.QuerySet):
    def active(self):
        return self.filter(active=True)

    def has_issues(self):
        return self.filter(structure__in=(ISSUES_AND_VOLUMES, ISSUES_ONLY))

    def has_individual_publications(self):
        return self.filter(structure=INDIVIDUAL_PUBLICATIONS)


class IssueQuerySet(models.QuerySet):
    def open_or_published(self):
        return self.filter(models.Q(status=STATUS_PUBLICLY_OPEN) |
                           models.Q(status=STATUS_PUBLISHED))

    def published(self):
        return self.filter(status=STATUS_PUBLISHED)

    def in_draft(self):
        return self.filter(status=STATUS_DRAFT)

    def for_journal(self, journal_name):
        return self.filter(
            models.Q(in_volume__in_journal__name=journal_name) |
            models.Q(in_journal__name=journal_name))

    def get_current_issue(self):
        return self.published(
            start_date__lte=timezone.now(), until_date__gte=timezone.now()).first()


class PublicationQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=PUBLICATION_PUBLISHED).filter(
            models.Q(in_issue__status=STATUS_PUBLISHED) | models.Q(in_journal__active=True))

    def unpublished(self):
        return self.exclude(status=PUBLICATION_PUBLISHED)

    def in_draft(self):
        return self.filter(in_issue__status=STATUS_DRAFT)

    def drafts(self):
        return self.filter(status=STATUS_DRAFT)

    def for_subject(self, subject_code):
        return self.filter(
            models.Q(subject_area=subject_code) |
            models.Q(secondary_areas__contains=[subject_code]))

    def for_journal(self, journal_name):
        return self.filter(
            models.Q(in_issue__in_volume__in_journal__name=journal_name) |
            models.Q(in_issue__in_journal__name=journal_name) |
            models.Q(in_journal__name=journal_name))

    def most_cited(self, n_returns=5):
        return self.order_by('-number_of_citations')[:n_returns]
