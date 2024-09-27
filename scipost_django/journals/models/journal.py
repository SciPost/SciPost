__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
from itertools import chain
import json

from django.db import models
from django.db.models import Avg, F
from django.urls import reverse
from django.utils import timezone

from scipost.fields import ChoiceArrayField
from series.models import Collection

from ..constants import (
    PUBLISHABLE_OBJECT_TYPE_CHOICES,
    get_default_acceptance_criteria,
    get_publishable_object_types_default_list,
    get_submission_object_types_default,
    JOURNAL_STRUCTURE,
    ISSUES_AND_VOLUMES,
    ISSUES_ONLY,
)
from ..managers import JournalQuerySet
from ..validators import doi_journal_validator


def cost_default_value():
    return {"default": 400}


class Journal(models.Model):
    """Journal is a container of Publications, with a unique issn and doi_label.

    Publications may be categorized into issues or issues and volumes.

    Each Journal falls under the auspices of a specific College, which is ForeignKeyed.
    The only exception is Selections, which does not point to any College
    (in fact: it falls under the auspices of all colleges at the same time).

    A Journal's AcademicField is indirectly specified via the College, since
    College has a ForeignKey to AcademicField.

    Specialties can optionally be specified (and should be consistent with the
    College's `acad_field`). If none are given, the Journal operates field-wide.
    """

    college = models.ForeignKey(
        "colleges.College", on_delete=models.PROTECT, related_name="journals"
    )

    specialties = models.ManyToManyField(
        "ontology.Specialty", blank=True, related_name="journals"
    )

    name = models.CharField(max_length=256, unique=True)
    name_abbrev = models.CharField(
        max_length=128,
        default="SciPost [abbrev]",
        help_text="Abbreviated name (for use in citations)",
    )

    doi_label = models.CharField(
        max_length=200, unique=True, db_index=True, validators=[doi_journal_validator]
    )
    issn = models.CharField(max_length=16, default="2542-4653", blank=True)

    active = models.BooleanField(default=True)

    submission_allowed = models.BooleanField(default=True)

    publishable_object_types = ChoiceArrayField(
        models.CharField(max_length=24, choices=PUBLISHABLE_OBJECT_TYPE_CHOICES),
        default=get_publishable_object_types_default_list,
    )
    submission_object_types = models.JSONField(
        default=get_submission_object_types_default,
    )

    structure = models.CharField(
        max_length=2, choices=JOURNAL_STRUCTURE, default=ISSUES_AND_VOLUMES
    )

    refereeing_period = models.DurationField(default=datetime.timedelta(days=28))
    assignment_period = models.DurationField(default=datetime.timedelta(days=28))

    style = models.TextField(
        blank=True,
        null=True,
        help_text=(
            "CSS styling for the journal; the Journal's DOI " "should be used as class"
        ),
    )

    # For Journals list page
    oneliner = models.TextField(
        blank=True,
        help_text="One-line description, for Journal card. You can use markup",
    )
    blurb = models.TextField(default="[To be filled in; you can use markup]")
    list_order = models.PositiveSmallIntegerField(default=100)

    # For manuscript preparation: templates are given by the SubmissionTemplate related objects

    # For the author guidelines page:
    required_article_elements = models.TextField(
        default="[To be filled in; you can use markup]"
    )
    # For about page:
    description = models.TextField(default="[To be filled in; you can use markup]")
    scope = models.TextField(default="[To be filled in; you can use markup]")
    content = models.TextField(default="[To be filled in; you can use markup]")
    acceptance_criteria = models.JSONField(default=get_default_acceptance_criteria)

    submission_insert = models.TextField(
        blank=True, null=True, default="[Optional; you can use markup]"
    )

    minimal_nr_of_reports = models.PositiveSmallIntegerField(
        help_text=(
            "Minimal number of substantial Reports required "
            "before an acceptance motion can be formulated"
        ),
        default=1,
    )

    has_DOAJ_Seal = models.BooleanField(default=False)

    has_CLOCKSS = models.BooleanField(default=True)

    # Templates
    template_latex_tgz = models.FileField(
        verbose_name="Template (LaTeX, gzipped tarball)",
        help_text="Gzipped tarball of the LaTeX template package",
        upload_to="UPLOADS/TEMPLATES/latex/%Y/",
        max_length=256,
        blank=True,
    )
    template_docx = models.FileField(
        verbose_name="Template (.docx)",
        help_text=".docx template",
        upload_to="UPLOADS/TEMPLATES/docx/%Y/",
        max_length=256,
        blank=True,
    )

    alternative_journals = models.ManyToManyField("self", blank=True)

    # Cost per publication information
    cost_info = models.JSONField(default=cost_default_value)

    # Calculated fields (to save CPU; field name always starts with cf_)
    cf_metrics = models.JSONField(default=dict)

    objects = JournalQuerySet.as_manager()

    class Meta:
        ordering = ["college__acad_field", "list_order"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Return Journal's homepage url."""
        return reverse("scipost:journal_detail", args=(self.doi_label,))

    @property
    def doi_string(self):
        """Return DOI including the SciPost registrant prefix."""
        return "10.21468/" + self.doi_label

    @property
    def has_issues(self):
        return self.structure in (ISSUES_AND_VOLUMES, ISSUES_ONLY)

    @property
    def has_volumes(self):
        return self.structure in (ISSUES_AND_VOLUMES)

    @property
    def has_collections(self):
        return Collection.objects.filter(series__container_journals=self).exists()

    @property
    def expectations(self):
        """Return a list of tuples with the acceptance expectations for this Journal."""
        sections = self.acceptance_criteria.get("sections", [])
        criteria = [
            s.get("criteria", {}).items()
            for s in sections
            if s.get("type", "") == "expectations"
        ]
        return list(chain(*criteria))

    @property
    def is_flagship(self):
        """
        Return True if this Journal is a flagship Journal,
        i.e. if its name is of the form "SciPost [Field]".
        """
        return self.name == "SciPost " + self.college.acad_field.name

    def get_issues(self):
        from journals.models import Issue

        if self.structure == ISSUES_AND_VOLUMES:
            return Issue.objects.filter(in_volume__in_journal=self).published()
        elif self.structure == ISSUES_ONLY:
            return self.issues.open_or_published()
        return Issue.objects.none()

    def get_latest_issue(self):
        """Get latest existing Issue in database irrespective of its status."""
        from journals.models import Issue

        if self.structure == ISSUES_ONLY:
            return self.issues.order_by("-until_date").first()
        if self.structure == ISSUES_AND_VOLUMES:
            return (
                Issue.objects.filter(in_volume__in_journal=self)
                .order_by("-until_date")
                .first()
            )
        return None

    def get_latest_volume(self):
        """Get latest existing Volume in database irrespective of its status."""
        if self.structure == ISSUES_AND_VOLUMES:
            return self.volumes.order_by("-until_date").first()
        return None

    def get_publications(self):
        from journals.models import Publication

        if self.structure == ISSUES_AND_VOLUMES:
            return Publication.objects.filter(in_issue__in_volume__in_journal=self)
        elif self.structure == ISSUES_ONLY:
            return Publication.objects.filter(in_issue__in_journal=self)
        return self.publications.all()

    def nr_publications(self, tier=None, year=None):
        publications = self.get_publications()
        if year:
            publications = publications.filter(publication_date__year=year)
        if tier:
            publications = publications.filter(
                accepted_submission__eicrecommendations__recommendation=tier
            )
        return publications.count()

    def avg_processing_duration(self):
        from journals.models import Publication

        duration = Publication.objects.filter(
            in_issue__in_volume__in_journal=self
        ).aggregate(avg=Avg(F("publication_date") - F("submission_date")))["avg"]
        if duration:
            return duration.total_seconds() / 86400
        return 0

    def citation_rate(self, tier=None):
        """Return the citation rate in units of nr citations per article per year."""
        publications = self.get_publications()
        if tier:
            publications = publications.filter(
                accepted_submission__eicrecommendations__recommendation=tier
            )
        ncites = 0
        deltat = 1  # to avoid division by zero
        for pub in publications:
            if pub.citedby and pub.latest_citedby_update:
                ncites += len(pub.citedby)
                deltat += (pub.latest_citedby_update.date() - pub.publication_date).days
        return ncites * 365.25 / deltat

    def nr_citations(self, year, specialty=None):
        publications = self.get_publications()
        if specialty:
            publications = publications.filter(specialties=specialty)

        return publications.citations_in_year(year)

    def nr_citations_per_year(self):
        publications = self.get_publications()

        return publications.citations_per_year()

    def citedby_impact_factor(self, year, specialty=None):
        """Compute the journals' impact factor for a given year.

        Optionally, filter publications by specialty.
        """
        publications = self.get_publications()
        if specialty:
            publications = publications.filter(specialties=specialty)

        return publications.impact_factor(year)

    def citedby_citescore(self, year, specialty=None):
        """Compute the journals' CiteScore for a given year.

        Optionally, filter publications by specialty.
        """
        publications = self.get_publications()
        if specialty:
            publications = publications.filter(specialties=specialty)

        return publications.citescore(year)

    def cost_per_publication(self, year):
        try:
            return int(self.cost_info[str(year)])
        except KeyError:
            return int(self.cost_info["default"])

    def update_cf_metrics(self):
        """
        Update the `cf_metrics` calculated field for this Journal.
        """
        publications = self.get_publications()
        from submissions.models import Submission

        if publications:
            pubyears = [
                year
                for year in range(
                    publications.last().publication_date.year, timezone.now().year
                )
            ]
        else:
            pubyears = [timezone.now().year]
        from submissions.models import Submission

        submissions = Submission.objects.filter(
            submitted_to=self, is_resubmission_of__isnull=True
        )
        self.cf_metrics["nr_publications"] = {
            "title": "Number of publications per year",
            "years": pubyears,
            "nr_publications": {
                "all": [
                    publications.filter(publication_date__year=year).count()
                    for year in pubyears
                ]
            },
        }
        self.cf_metrics["nr_submissions"] = {
            "title": "Number of submissions per year",
            "years": pubyears,
            "nr_submissions": {
                "all": [
                    submissions.filter(submission_date__year=year).count()
                    for year in pubyears
                ]
            },
        }
        self.cf_metrics["nr_citations"] = {
            "title": "Number of citations per year",
            "years": pubyears,
            "nr_citations": {"all": [self.nr_citations(year) for year in pubyears]},
        }
        self.cf_metrics["citedby_citescore"] = {
            "title": "CiteScore",
            "years": pubyears,
            "citedby_citescore": {
                "all": [self.citedby_citescore(year) for year in pubyears]
            },
        }
        self.cf_metrics["citedby_impact_factor"] = {
            "title": "Impact Factor",
            "years": pubyears,
            "citedby_impact_factor": {
                "all": [self.citedby_impact_factor(year) for year in pubyears]
            },
        }
        for specialty in self.specialties.all():
            self.cf_metrics["nr_publications"]["nr_publications"][specialty.slug] = [
                publications.filter(
                    specialties=specialty, publication_date__year=year
                ).count()
                for year in pubyears
            ]
            self.cf_metrics["nr_submissions"]["nr_submissions"][specialty.slug] = [
                submissions.filter(
                    specialties=specialty, submission_date__year=year
                ).count()
                for year in pubyears
            ]
            self.cf_metrics["nr_citations"]["nr_citations"][specialty.slug] = [
                self.nr_citations(year, specialty) for year in pubyears
            ]
            self.cf_metrics["citedby_citescore"]["citedby_citescore"][
                specialty.slug
            ] = [self.citedby_citescore(year, specialty) for year in pubyears]
            self.cf_metrics["citedby_impact_factor"]["citedby_impact_factor"][
                specialty.slug
            ] = [self.citedby_impact_factor(year, specialty) for year in pubyears]
        self.save()
