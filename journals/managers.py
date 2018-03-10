from django.db import models
from django.utils import timezone

from .constants import STATUS_PUBLISHED, STATUS_DRAFT, PUBLICATION_PUBLISHED, ISSUES_AND_VOLUMES,\
    ISSUES_ONLY


class JournalQuerySet(models.QuerySet):
    def active(self):
        return self.filter(active=True)

    def has_issues(self):
        return self.filter(structure__in=(ISSUES_AND_VOLUMES, ISSUES_ONLY))


class IssueQuerySet(models.QuerySet):
    def published(self, journal=None):
        issues = self.filter(status=STATUS_PUBLISHED)
        if journal:
            issues.filter(in_volume__in_journal=journal)
        return issues

    def in_draft(self, journal=None):
        issues = self.filter(status=STATUS_DRAFT)
        if journal:
            issues.filter(in_volume__in_journal=journal)
        return issues

    def get_current_issue(self):
        return self.published(
            start_date__lte=timezone.now(), until_date__gte=timezone.now()).first()


class PublicationQuerySet(models.QuerySet):
    def published(self, **kwargs):
        return self.filter(status=PUBLICATION_PUBLISHED).filter(
            models.Q(in_issue__status=STATUS_PUBLISHED) | models.Q(in_journal__active=True))

    def unpublished(self):
        return self.exclude(status=PUBLICATION_PUBLISHED)

    def in_draft(self):
        return self.filter(in_issue__status=STATUS_DRAFT)

    def drafts(self):
        return self.filter(status=STATUS_DRAFT)
