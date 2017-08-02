from django.db import models
from django.http import Http404
from django.utils import timezone

from .constants import STATUS_PUBLISHED, STATUS_DRAFT


class JournalManager(models.Manager):
    def active(self):
        return self.filter(active=True)


class IssueManager(models.Manager):
    def get_published(self, *args, **kwargs):
        try:
            return self.published(*args, **kwargs)[0]
        except IndexError:
            raise Http404

    def published(self, journal=None, **kwargs):
        issues = self.filter(status=STATUS_PUBLISHED, **kwargs)
        if journal:
            issues.filter(in_volume__in_journal=journal)
        return issues

    def in_draft(self, journal=None, **kwargs):
        issues = self.filter(status=STATUS_DRAFT, **kwargs)
        if journal:
            issues.filter(in_volume__in_journal=journal)
        return issues

    def get_current_issue(self, *args, **kwargs):
        return self.published(start_date__lte=timezone.now(),
                              until_date__gte=timezone.now(),
                              **kwargs).order_by('-until_date').first()

    def get_last_filled_issue(self, *args, **kwargs):
        return self.published(publication__isnull=False,
                              **kwargs).order_by('-until_date').first()


class PublicationManager(models.Manager):
    def get_published(self, *args, **kwargs):
        try:
            return self.published(*args, **kwargs)[0]
        except IndexError:
            raise Http404

    def published(self, **kwargs):
        return self.filter(in_issue__status=STATUS_PUBLISHED, **kwargs)

    def in_draft(self, **kwargs):
        return self.filter(in_issue__status=STATUS_DRAFT, **kwargs)
