__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from decimal import Decimal
from string import Template as string_Template
import re
from typing import TYPE_CHECKING

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Min, Sum, OuterRef, Exists, Q
from django.urls import reverse
from django.utils.functional import cached_property

from ..constants import (
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    PUBLICATION_PUBLISHED,
    CCBY4,
    CC_LICENSES,
    CC_LICENSES_URI,
    PUBLICATION_STATUSES,
)
from ..helpers import paper_nr_string
from ..managers import PublicationQuerySet
from ..validators import doi_publication_validator

from common.utils import get_current_domain
from finances.models import PubFrac
from scipost.constants import SCIPOST_APPROACHES
from scipost.fields import ChoiceArrayField


if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager
    from production.models import ProofsRepository
    from profiles.models import Profile


class PublicationAuthorsTable(models.Model):
    """
    PublicationAuthorsTable represents an author of a Publication.

    Fields:

    * publication
    * profile
    * affiliations: for this author/Publication (supersede profile.affiliations)
    * order: the ordinal position of this author in this Publication's list of authors.
    """

    publication = models.ForeignKey(
        "journals.Publication", on_delete=models.CASCADE, related_name="authors"
    )
    profile = models.ForeignKey["Profile"](
        "profiles.Profile", on_delete=models.PROTECT, blank=True, null=True
    )
    affiliations = models.ManyToManyField("organizations.Organization", blank=True)
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ("order",)

    def __str__(self):
        return str(self.profile)

    def save(self, *args, **kwargs):
        """Auto increment order number if not explicitly set."""
        if not self.order:
            self.order = self.publication.authors.count() + 1
        return super().save(*args, **kwargs)

    def is_empty(self) -> bool:
        """Check if object is a temporary placeholder."""
        return self.profile is None

    @property
    def first_name(self) -> str:
        """Return first name of author. If not available, return None."""
        return self.profile.first_name if self.profile else None

    @property
    def last_name(self) -> str:
        """Return last name of author. If not available, return None."""
        return self.profile.last_name if self.profile else None


class Publication(models.Model):
    """A Publication is an object directly related to an accepted Submission.

    It contains metadata, the actual publication file, author data, etc. etc.
    It may be directly related to a Journal or to an Issue.
    """

    PUBTYPE_ARTICLE = "article"
    PUBTYPE_CODEBASE_RELEASE = "codebase_release"
    PUBTYPE_CHOICES = (
        (PUBTYPE_ARTICLE, "Article"),
        (PUBTYPE_CODEBASE_RELEASE, "Codebase release"),
    )
    pubtype = models.CharField(
        max_length=32,
        choices=PUBTYPE_CHOICES,
        default=PUBTYPE_ARTICLE,
    )

    # Publication data
    accepted_submission = models.ForeignKey(
        "submissions.Submission",
        on_delete=models.CASCADE,
    )
    in_issue = models.ForeignKey(
        "journals.Issue",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Assign either an Issue or Journal to the Publication",
    )
    in_journal = models.ForeignKey(
        "journals.Journal",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Assign either an Issue or Journal to the Publication",
    )
    paper_nr = models.PositiveSmallIntegerField()
    paper_nr_suffix = models.CharField(max_length=32, blank=True)
    status = models.CharField(
        max_length=8, choices=PUBLICATION_STATUSES, default=STATUS_DRAFT
    )

    # Core fields
    title = models.CharField(max_length=300)
    author_list = models.CharField(max_length=10000, verbose_name="author list")
    abstract = models.TextField()
    abstract_jats = models.TextField(
        blank=True,
        default="",
        help_text="JATS version of abstract for Crossref deposit",
    )
    pdf_file = models.FileField(
        upload_to="UPLOADS/PUBLICATIONS/%Y/%m/", max_length=200, blank=True
    )

    # Ontology-based semantic linking
    acad_field = models.ForeignKey(
        "ontology.AcademicField", on_delete=models.PROTECT, related_name="publications"
    )
    specialties = models.ManyToManyField(
        "ontology.Specialty", related_name="publications"
    )
    topics = models.ManyToManyField("ontology.Topic", blank=True)
    approaches = ChoiceArrayField(
        models.CharField(max_length=24, choices=SCIPOST_APPROACHES),
        blank=True,
        null=True,
    )

    cc_license = models.CharField(max_length=32, choices=CC_LICENSES, default=CCBY4)

    # Funders
    grants = models.ManyToManyField("funders.Grant", blank=True)
    funders_generic = models.ManyToManyField(
        "funders.Funder", blank=True
    )  # not linked to a grant

    # Metadata
    metadata = models.JSONField(default=dict, blank=True, null=True)
    metadata_xml = models.TextField(blank=True)  # for Crossref deposit
    metadata_DOAJ = models.JSONField(default=dict, blank=True, null=True)
    doi_label = models.CharField(
        max_length=200,
        unique=True,
        db_index=True,
        validators=[doi_publication_validator],
    )
    doideposit_needs_updating = models.BooleanField(default=False)
    citedby = models.JSONField(default=dict, blank=True, null=True)
    number_of_citations = models.PositiveIntegerField(default=0)

    # To handle cases without parsable author info (e.g. docx)
    author_info_source = models.TextField(blank=True, null=True)

    # Date fields
    submission_date = models.DateField(verbose_name="submission date")
    acceptance_date = models.DateField(verbose_name="acceptance date")
    publication_date = models.DateField(verbose_name="publication date")
    latest_citedby_update = models.DateTimeField(null=True, blank=True)
    latest_metadata_update = models.DateTimeField(blank=True, null=True)
    latest_activity = models.DateTimeField(
        auto_now=True
    )  # Needs `auto_now` as its not explicity updated anywhere?

    # Calculated fields
    cf_citation = models.CharField(
        max_length=1024,
        blank=True,
        help_text="NB: calculated field. Do not modify.",
    )
    cf_author_affiliation_indices_list = ArrayField(
        ArrayField(
            models.PositiveSmallIntegerField(blank=True, null=True), default=list
        ),
        default=list,
        help_text="NB: calculated field. Do not modify.",
    )

    objects = PublicationQuerySet.as_manager()

    if TYPE_CHECKING:
        authors = RelatedManager[PublicationAuthorsTable]

    class Meta:
        default_related_name = "publications"
        ordering = ("-publication_date", "-paper_nr")

    def __str__(self):
        return "{cite}, {title} by {authors}, {date}".format(
            cite=self.citation,
            title=self.title[:30],
            authors=self.author_list[:30],
            date=self.publication_date.strftime("%Y-%m-%d"),
        )

    def clean(self):
        """Check if either a valid Journal or Issue is assigned to the Publication."""
        if not (self.in_journal or self.in_issue):
            raise ValidationError(
                {
                    "in_journal": ValidationError(
                        "Either assign a Journal or Issue to this Publication",
                        code="required",
                    ),
                    "in_issue": ValidationError(
                        "Either assign a Journal or Issue to this Publication",
                        code="required",
                    ),
                }
            )
        if self.in_journal and self.in_issue:
            # Assigning both a Journal and an Issue will screw up the database
            raise ValidationError(
                {
                    "in_journal": ValidationError(
                        "Either assign only a Journal or Issue to this Publication",
                        code="invalid",
                    ),
                    "in_issue": ValidationError(
                        "Either assign only a Journal or Issue to this Publication",
                        code="invalid",
                    ),
                }
            )
        if self.in_issue and not self.get_journal().has_issues:
            # Assigning both a Journal and an Issue will screw up the database
            raise ValidationError(
                {
                    "in_issue": ValidationError(
                        "This journal does not allow the use of Issues", code="invalid"
                    ),
                }
            )
        if self.in_journal and self.get_journal().has_issues:
            # Assigning both a Journal and an Issue will screw up the database
            raise ValidationError(
                {
                    "in_journal": ValidationError(
                        "This journal does not allow the use of individual Publications",
                        code="invalid",
                    ),
                }
            )

    def get_absolute_url(self):
        return reverse("scipost:publication_detail", args=(self.doi_label,))

    def get_cc_license_URI(self):
        for key, val in CC_LICENSES_URI:
            if key == self.cc_license:
                return val
        raise KeyError

    def get_all_affiliations(self):
        """
        Returns all author affiliations.
        """
        from organizations.models import Organization

        return (
            Organization.objects.filter(publicationauthorstable__publication=self)
            .annotate(order=Min("publicationauthorstable__order"))
            .order_by("order")
        )

    def get_author_affiliation_indices_list(self):
        """
        Return a list containing for each author an ordered list of affiliation indices.

        This is for display on the publication detail page,
        and is a calculated field (saved in the model) to avoid
        unnecessary db queries (problematic for papers with large number of authors).
        """
        if len(self.cf_author_affiliation_indices_list) > 0:
            return self.cf_author_affiliation_indices_list

        indexed_author_list = []
        pub_affiliations = self.get_all_affiliations()
        pub_authors = self.authors.all().prefetch_related("affiliations")

        for author in pub_authors:
            affnrs = []
            for idx, aff in enumerate(pub_affiliations):
                if aff in author.affiliations.all():
                    affnrs.append(idx + 1)

            # If no affiliation is found, add a None to the list
            # Prevents crashes since Django v4
            if len(affnrs) == 0:
                affnrs = [None]

            indexed_author_list.append(affnrs)

        # Since nested ArrayFields must have the same dimension,
        # we pad the "empty" entries with Null:
        max_length = 0
        for entry in indexed_author_list:
            max_length = max(max_length, len(entry))

        padded_list = []
        for entry in indexed_author_list:
            padded_entry = entry + [None] * (max_length - len(entry))
            padded_list.append(padded_entry)

        # Save into the calculated field for future purposes.
        Publication.objects.filter(id=self.id).update(
            cf_author_affiliation_indices_list=padded_list
        )
        return padded_list

    def get_all_funders(self):
        from funders.models import Funder

        return Funder.objects.annotate(
            has_publication_in_grants=Exists(self.grants.filter(funder=OuterRef("pk"))),
            has_publication_in_funders_generic=Exists(
                self.funders_generic.filter(pk=OuterRef("pk"))
            ),
        ).filter(
            Q(has_publication_in_grants=True)
            | Q(has_publication_in_funders_generic=True)
        )

    def get_affiliations(self):
        """Returns the Organizations mentioned in author affiliations."""
        from organizations.models import Organization

        return Organization.objects.filter(
            publicationauthorstable__publication=self
        ).distinct()

    @property
    def doi_string(self) -> str:
        return "10.21468/" + self.doi_label

    @property
    def is_draft(self) -> bool:
        """Check if the publication is in draft status, awaiting to be published."""
        return self.status == STATUS_DRAFT

    @property
    def is_published(self) -> bool:
        if self.status != PUBLICATION_PUBLISHED:
            return False

        if self.in_issue:
            return self.in_issue.status == STATUS_PUBLISHED
        elif self.in_journal:
            return self.in_journal.active
        return False

    @property
    def has_abstract_jats(self) -> bool:
        """Check if there is a JATS version of the abstract used for Crossref deposits."""
        return self.abstract_jats != ""

    @property
    def has_xml_metadata(self) -> bool:
        """Check if there is XML metadata used for Crossref deposits."""
        return self.metadata_xml != ""

    @property
    def BiBTeX(self):
        bibtex_entry = ("@Article{%s,\n\ttitle={{%s}},\n\tauthor={%s},\n") % (
            self.doi_string,
            self.title,
            self.author_list.replace(",", " and"),
        )
        if self.in_issue:
            if self.in_issue.in_volume:
                bibtex_entry += "\tjournal={%s},\n\tvolume={%i},\n" % (
                    self.in_issue.in_volume.in_journal.name_abbrev,
                    self.in_issue.in_volume.number,
                )
            elif self.in_issue.in_journal:
                bibtex_entry += (
                    "\tjournal={%s},\n" % self.in_issue.in_journal.name_abbrev
                )
        elif self.in_journal:
            bibtex_entry += "\tjournal={%s},\n" % self.in_journal.name_abbrev
        bibtex_entry += (
            "\tpages={%s},\n"
            "\tyear={%s},\n"
            "\tpublisher={SciPost},\n"
            "\tdoi={%s},\n"
            "\turl={https://%s/%s},\n"
            "}"
        ) % (
            self.get_paper_nr(),
            self.publication_date.strftime("%Y"),
            self.doi_string,
            get_current_domain(),
            self.doi_string,
        )
        return bibtex_entry

    def resources_as_md(self):
        """Return a Markdown string representing the list of resources."""
        if self.resources.all():
            resources_md = "## Resources:\n\n"
            for resource in self.resources.all():
                resources_md += (
                    f"* {resource.get__type_display()} "
                    f"at [{resource.url}]({resource.url})\n"
                )
            return resources_md
        return None

    @property
    def has_citation_list(self):
        return (
            "citation_list" in self.metadata and len(self.metadata["citation_list"]) > 0
        )

    @property
    def has_funding_statement(self):
        return (
            "funding_statement" in self.metadata and self.metadata["funding_statement"]
        )

    @property
    def expenditures(self):
        """The expenditures (as defined by the Journal) to produce this Publication."""
        return self.get_journal().cost_per_publication(self.publication_date.year)

    def recalculate_pubfracs(self):
        """Recalculates PubFracs using the balanced affiliations algorithm."""
        # First, remove non-affiliation-related PubFracs
        aff_ids = [aff.id for aff in self.get_affiliations()]
        PubFrac.objects.filter(publication=self).exclude(
            organization__pk__in=aff_ids
        ).delete()
        # Now recreate according to the balanced affiliations algorithm
        nr_authors = self.authors.all().count()
        affiliations = self.get_affiliations()
        for org in affiliations.all():
            pubfrac, created = PubFrac.objects.get_or_create(
                publication=self, organization=org
            )
        fraction = {}
        for org in affiliations.all():
            fraction[org.id] = 0
        for author in self.authors.all():
            nr_affiliations = author.affiliations.all().count()
            for aff in author.affiliations.all():
                fraction[aff.id] += 1.0 / (nr_authors * nr_affiliations)
        for org in affiliations.all():
            pubfrac, created = PubFrac.objects.get_or_create(
                publication=self,
                organization=org,
            )
            # ensure 3 digit accuracy for all fractions through integer cast
            pubfrac.fraction = 0.001 * int(1000 * fraction[org.id])
            pubfrac.save()
        self.ensure_pubfracs_sum_to_1()

    def ensure_pubfracs_sum_to_1(self):
        """Ensure sum is 1 by putting any difference in the largest PubFrac."""
        pubfrac_max = self.pubfracs.order_by("-fraction").first()
        sum_pubfracs = self.pubfracs.aggregate(Sum("fraction"))["fraction__sum"]
        pubfrac_max.fraction += 1 - sum_pubfracs
        pubfrac_max.save()

    @property
    def pubfracs_sum_to_1(self):
        """Checks that the support fractions sum up to one."""
        return self.pubfracs.aggregate(Sum("fraction"))["fraction__sum"] == 1

    @property
    def proofs_repository(self) -> "ProofsRepository":
        """Return the proofs repository for the publication."""
        return self.accepted_submission.production_stream.proofs_repository

    @property
    def compensated_expenditures(self):
        """Compensated part of expenditures for this Publication."""
        qs = self.pubfracs.filter(compensated_by__isnull=False)
        # Use the fraction to obtain an accurate result
        return (
            qs.aggregate(Sum("fraction"))["fraction__sum"] * self.expenditures
            if qs.exists()
            else 0
        )

    @property
    def uncompensated_expenditures(self):
        """Unompensated part of expenditures for this Publication."""
        return self.expenditures - self.compensated_expenditures

    @property
    def citation(self):
        if self.cf_citation:
            return self.cf_citation
        citation = ""
        """Return Publication name in the preferred citation format."""
        if self.in_issue and self.in_issue.in_volume:
            citation = "{journal} {volume}, {paper_nr} ({year})".format(
                journal=self.in_issue.in_volume.in_journal.name_abbrev,
                volume=self.in_issue.in_volume.number,
                paper_nr=self.get_paper_nr(),
                year=self.publication_date.strftime("%Y"),
            )
        elif self.in_issue and self.in_issue.in_journal:
            citation = "{journal} {issue}, {paper_nr} ({year})".format(
                journal=self.in_issue.in_journal.name_abbrev,
                issue=self.in_issue.number,
                paper_nr=self.get_paper_nr(),
                year=self.publication_date.strftime("%Y"),
            )
        elif self.in_journal:
            citation = "{journal} {paper_nr} ({year})".format(
                journal=self.in_journal.name_abbrev,
                paper_nr=self.get_paper_nr(),
                year=self.publication_date.strftime("%Y"),
            )
        else:
            citation = "{paper_nr} ({year})".format(
                paper_nr=self.get_paper_nr(), year=self.publication_date.strftime("%Y")
            )
        self.cf_citation = citation
        self.save()
        return citation

    def get_journal(self):
        if self.in_journal:
            return self.in_journal
        elif self.in_issue.in_journal:
            return self.in_issue.in_journal
        return self.in_issue.in_volume.in_journal

    def journal_issn(self):
        return self.get_journal().issn

    def get_volume(self):
        if self.in_issue and self.in_issue.in_volume:
            return self.in_issue.in_volume
        return None

    def get_paper_nr(self):
        """Returns the paper number (including possible suffixes) as a string."""
        s = f"{self.paper_nr}" if self.in_journal else paper_nr_string(self.paper_nr)
        return f"{s}{f'-{self.paper_nr_suffix}' if self.paper_nr_suffix else ''}"

    def citation_rate(self):
        """Returns the citation rate in units of nr citations per article per year."""
        if self.citedby and self.latest_citedby_update:
            ncites = len(self.citedby)
            deltat = (self.latest_citedby_update.date() - self.publication_date).days
            return ncites * 365.25 / deltat
        else:
            return 0

    def get_issue_related_publications(self):
        """Return 4 Publications within same Issue."""
        return (
            Publication.objects.published()
            .filter(in_issue=self.in_issue)
            .exclude(id=self.id)[:4]
        )

    @property
    def bundle(self):
        """Returns a QuerySet of all Publications with same DOI anchor."""
        doi_anchor = self.doi_label.partition("-")[0]
        return Publication.objects.filter(
            models.Q(doi_label=doi_anchor)
            | models.Q(doi_label__startswith=f"{doi_anchor}-")
        ).order_by("doi_label")

    @cached_property
    def tex_contents(self) -> str | None:
        return self.author_info_source or self.proofs_repository.fetch_tex()

    @cached_property
    def tex_affiliations(self) -> list[tuple[str, str]]:
        """
        Extracts the affiliations from the TeX contents, constructing a list
        with each affiliation as an (identifier, text) pair
        Matches the pattern: `{\\bf #} Affiliation Text ...\\\\`
        Returns a list of tuples with the affiliation identifier (number) and the affiliation text.
        """
        affiliations_block = re.search(
            r"%+ TODO: AFFILIATIONS.*?%+ END TODO: AFFILIATIONS",
            self.tex_contents or "",
            re.DOTALL,
        )

        if affiliations_block is None:
            return []

        matches = re.findall(
            r"\n(?:\{\\bf\s([^%]+?)\})?\s?([^%]+?)\n(?:\\\\|%)",
            affiliations_block.group(),
            re.DOTALL,
        )

        return [
            (number or f"UN_{i}", text.replace("\\\\", " ").strip())
            for i, (number, text) in enumerate(matches)
        ]

    @cached_property
    def tex_author_info(self) -> list[tuple[str, list[str]]]:
        """
        Returns a list of tuples with the author name and a list of superscripts.
        """

        authors_block = re.search(
            r"%+ TODO: AUTHORS(.*?)%+ END TODO: AUTHORS",
            self.tex_contents or "",
            re.DOTALL,
        )
        if authors_block is None:
            # If matching against the tex file fails, we use the author_list of the submission.
            return [(author.strip(), []) for author in self.author_list.split(",")]

        author_lines = authors_block.group(1).strip().split("\n")

        def extract_author_info(line: str) -> tuple[str, list[str]]:
            """Extracts the superscripts from a text."""
            author_match = re.match(r"^(?:\\orcidlink\{.*?\}\\?\W?)?([^\\]+)", line)
            superscripts_match = re.match(r".*?\\textsuperscript\{(.*?)\}", line)

            author_text = author_match.group(1) if author_match else ""
            superscripts_text = (
                superscripts_match.group(1) if superscripts_match else ""
            )

            # Remove any trailing or leading "and"s.
            author_text = re.sub(r"(?:^and(\W)|(\W)and$)", r"\1", author_text).strip()

            # Prepend a comma to every $...$ expression to split them later
            superscripts_text = re.sub(r"(\$.+?\$)", r",\1", superscripts_text)

            return (
                author_text.strip(),
                [superscript.strip() for superscript in superscripts_text.split(",")],
            )

        return [extract_author_info(line) for line in author_lines]

    def reset_author_associations(self) -> None:
        """Deletes all PublicationAuthorsTable entries and repopulates it based on the tex file uploaded on git."""
        from profiles.models import Profile

        PublicationAuthorsTable.objects.filter(publication=self).delete()

        # We add the succesful authors from the author_render_list to the PublicationAuthorsTable.
        author_entries: list[PublicationAuthorsTable] = []
        author_names = [name for name, _ in self.tex_author_info]
        for i, name in enumerate(author_names):
            profile_matches = list(Profile.objects.search(name))
            profile = profile_matches[0] if profile_matches else None

            author_entries.append(
                PublicationAuthorsTable(
                    publication=self,
                    profile=profile,
                    order=i + 1,
                )
            )

        PublicationAuthorsTable.objects.bulk_create(author_entries)

        self.cf_author_affiliation_indices_list = []
        if author_names:
            self.author_list = ", ".join(author_names)

        self.save()


class Reference(models.Model):
    """A Refence is a reference used in a specific Publication."""

    reference_number = models.IntegerField()
    publication = models.ForeignKey("journals.Publication", on_delete=models.CASCADE)

    authors = models.CharField(max_length=1028)
    citation = models.CharField(max_length=1028, blank=True)
    identifier = models.CharField(blank=True, max_length=128)
    link = models.URLField(blank=True)

    class Meta:
        unique_together = ("reference_number", "publication")
        ordering = ["reference_number"]
        default_related_name = "references"

    def __str__(self):
        return "[{}] {}, {}".format(
            self.reference_number, self.authors[:30], self.citation[:30]
        )
