__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import connection, models
from django.db.models import Q
from django.utils import timezone

from .constants import (
    STATUS_DRAFT,
    STATUS_PUBLICLY_OPEN,
    STATUS_PUBLISHED,
    PUBLICATION_PUBLISHED,
    ISSUES_AND_VOLUMES,
    ISSUES_ONLY,
    INDIVIDUAL_PUBLICATIONS,
)


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from journals.models.journal import Journal


class JournalQuerySet(models.QuerySet):
    def active(self):
        return self.filter(active=True)

    def submission_allowed(self):
        return self.filter(submission_allowed=True)

    def has_issues(self):
        return self.filter(structure__in=(ISSUES_AND_VOLUMES, ISSUES_ONLY))

    def has_individual_publications(self):
        return self.filter(structure=INDIVIDUAL_PUBLICATIONS)

    def get_publications(self):
        from journals.models.publication import Publication

        return Publication.objects.filter(
            Q(in_journal__in=self)
            | Q(in_issue__in_journal__in=self)
            | Q(in_issue__in_volume__in_journal__in=self)
        ).all()


class IssueQuerySet(models.QuerySet):
    def open_or_published(self):
        return self.filter(
            models.Q(status=STATUS_PUBLICLY_OPEN) | models.Q(status=STATUS_PUBLISHED)
        )

    def published(self):
        return self.filter(status=STATUS_PUBLISHED)

    def in_draft(self):
        return self.filter(status=STATUS_DRAFT)

    def for_journal(self, journal_name):
        return self.filter(
            models.Q(in_volume__in_journal__name=journal_name)
            | models.Q(in_journal__name=journal_name)
        )

    def get_current_issue(self):
        return self.published(
            start_date__lte=timezone.now(), until_date__gte=timezone.now()
        ).first()


class IssueManager(models.Manager.from_queryset(IssueQuerySet)):
    # Since Issue's `str` method requires these related fields, we prefetch them
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related(
                "proceedings",
                "in_volume",
                "in_volume__in_journal",
                "in_journal",
            )
        )


class PublicationQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=PUBLICATION_PUBLISHED).filter(
            models.Q(in_issue__status=STATUS_PUBLISHED)
            | models.Q(in_journal__active=True)
        )

    def unpublished(self):
        return self.exclude(status=PUBLICATION_PUBLISHED)

    def in_draft(self):
        return self.filter(in_issue__status=STATUS_DRAFT)

    def drafts(self):
        return self.filter(status=STATUS_DRAFT)

    def for_specialty(self, specialty):
        return self.filter(specialties__slug=specialty)

    def for_journal(self, journal_name):
        return self.filter(
            models.Q(in_issue__in_volume__in_journal__name=journal_name)
            | models.Q(in_issue__in_journal__name=journal_name)
            | models.Q(in_journal__name=journal_name)
        )

    def for_journals(self, journals: "models.QuerySet[Journal]"):
        return self.filter(
            models.Q(in_issue__in_volume__in_journal__in=journals)
            | models.Q(in_issue__in_journal__in=journals)
            | models.Q(in_journal__in=journals)
        )

    def most_cited(self, n_returns=5):
        return self.order_by("-number_of_citations")[:n_returns]

    def citations_in_year(self, year) -> int:
        """
        Returns the number of citations for all publications in the queryset for a given year.
        """
        if not self.exists():
            return 0

        query = (
            "SELECT COUNT(*) "
            "FROM ("
            "    SELECT jsonb_array_elements(citedby::jsonb) AS citation"
            "    FROM journals_publication"
            "    WHERE citedby <> '{}'::jsonb "
            f"   AND id IN ({', '.join(map(str, self.values_list('id', flat=True)))})"
            ") AS citations "
            f"WHERE citation->>'year' = '{year}'"
        )

        # Run the query
        with connection.cursor() as cursor:
            cursor.execute(query)
            citations = cursor.fetchone()

        if citations:
            return citations[0]

    def citations_per_year(self) -> dict[int, int]:
        """
        Returns a dictionary with year as key and number of citations as value.
        """
        if not self.exists():
            return {}

        query = (
            "SELECT CAST(citation->>'year' AS INTEGER), COUNT(*) "
            "FROM ("
            "    SELECT jsonb_array_elements(citedby::jsonb) AS citation"
            "    FROM journals_publication"
            "    WHERE citedby <> '{}'::jsonb "
            f"   AND id IN ({', '.join(map(str, self.values_list('id', flat=True)))})"
            ") AS citations "
            "GROUP BY citation->>'year' "
            "ORDER BY citation->>'year'"
        )

        # Run the query
        with connection.cursor() as cursor:
            cursor.execute(query)
            citations = cursor.fetchall()

        return dict(citations)

    def impact_factor(self, year):
        """
        Compute the impact factor for a given year YYYY, from Crossref cited-by data.

        This is defined as the total number of citations in year YYYY
        for all papers published in years YYYY-1 and YYYY-2, divided
        by the number of papers published in that same set of years.
        """
        qs = self.filter(
            publication_date__year__gte=int(year) - 2,
            publication_date__year__lte=int(year) - 1,
        )

        if not qs.exists():
            return 0

        query = (
            "SELECT COUNT(*) "
            "FROM ("
            "    SELECT jsonb_array_elements(citedby::jsonb) AS citation"
            "    FROM journals_publication"
            "    WHERE citedby <> '{}'::jsonb "
            f"   AND id IN ({', '.join(map(str, qs.values_list('id', flat=True)))})"
            ") AS citations "
            f"WHERE citation->>'year' = '{year}'"
        )

        # Run the query
        with connection.cursor() as cursor:
            cursor.execute(query)
            citations = cursor.fetchone()

        if citations:
            return citations[0] / qs.count()

    def citescore(self, year):
        """
        Compute the CiteScore for a given year YYYY, from Crossref cited-by data.

        This is defined as the total number of citations in years YYYY to YYYY-3
        for all papers published in years YYYY to YYYY-3, divided
        by the number of papers published in that same set of years.
        """
        qs = self.filter(
            publication_date__year__lte=int(year),
            publication_date__year__gte=int(year) - 3,
        )

        if not qs.exists():
            return 0

        query = (
            "SELECT COUNT(*) "
            "FROM ("
            "    SELECT jsonb_array_elements(citedby::jsonb) AS citation"
            "    FROM journals_publication"
            "    WHERE citedby <> '{}'::jsonb "
            f"   AND id IN ({', '.join(map(str, qs.values_list('id', flat=True)))})"
            ") AS citations "
            f"WHERE citation->>'year' IN ('{year}', '{int(year) - 1}', '{int(year) - 2}', '{int(year) - 3}')"
        )

        # Run the query
        with connection.cursor() as cursor:
            cursor.execute(query)
            citations = cursor.fetchone()

        if citations:
            return citations[0] / qs.count()


class PublicationResourceQuerySet(models.QuerySet):
    def current(self):
        return self.filter(deprecated=False)

    def source(self):
        return self.filter(_type=self.model.TYPE_SOURCE_REPO)

    def release(self):
        return self.filter(_type=self.model.TYPE_RELEASE_ARCHIVE_REPO)

    def live(self):
        return self.filter(_type=self.model.TYPE_LIVE_REPO)

    def sup_info(self):
        return self.filter(_type=self.model.TYPE_SUP_INFO)
