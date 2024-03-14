__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import hashlib
import os
import random
import re
import string

from datetime import datetime

from django import forms
from django.conf import settings
from django.db.models import Q, Max
from django.forms import BaseModelFormSet, modelformset_factory
from django.template import loader
from django.utils import timezone

import lxml.etree as ET
from html.entities import entitydefs

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, ButtonHolder, Submit
from crispy_bootstrap5.bootstrap5 import FloatingField
from dal import autocomplete
from common.forms import HTMXInlineCRUDModelForm

from journals.models.resource import PublicationResource
from journals.models.update import PublicationUpdate

from .constants import (
    STATUS_DRAFT,
    STATUS_PUBLICLY_OPEN,
    PUBLICATION_PREPUBLISHED,
    PUBLICATION_PUBLISHED,
)
from .exceptions import PaperNumberingError
from .models import (
    Issue,
    Publication,
    Reference,
    Volume,
    PublicationAuthorsTable,
)
from .utils import JournalUtils


from common.utils import get_current_domain, jatsify_tags
from finances.models import PubFrac
from funders.models import Grant, Funder
from journals.models import Journal
from mails.utils import DirectMailUtil
from organizations.models import Organization
from proceedings.models import Proceedings
from production.constants import PRODUCTION_STREAM_COMPLETED
from production.models import ProductionEvent
from scipost.forms import RequestFormMixin
from scipost.services import DOICaller
from submissions.models import Submission


class PublicationSearchForm(forms.Form):
    """Simple search form to filter a Publication queryset."""

    author = forms.CharField(max_length=100, required=False, label="Author(s)")
    title = forms.CharField(max_length=100, required=False)
    doi_label = forms.CharField(max_length=100, required=False)
    journal = forms.ModelChoiceField(queryset=Journal.objects.all(), required=False)
    proceedings = forms.ModelChoiceField(
        queryset=Proceedings.objects.all(), required=False
    )

    def __init__(self, *args, **kwargs):
        self.acad_field_slug = kwargs.pop("acad_field_slug")
        self.specialty_slug = kwargs.pop("specialty_slug")
        super().__init__(*args, **kwargs)
        if self.acad_field_slug and self.acad_field_slug != "all":
            self.fields["journal"].queryset = Journal.objects.filter(
                college__acad_field__slug=self.acad_field_slug
            )
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(FloatingField("author"), css_class="col-lg-6"),
                Div(FloatingField("title"), css_class="col-lg-6"),
                css_class="row mb-0",
            ),
            Div(
                Div(FloatingField("journal"), css_class="col-lg-6"),
                Div(FloatingField("doi_label"), css_class="col-lg-6"),
                css_class="row mb-0",
            ),
            Div(
                Div(FloatingField("proceedings"), css_class="col-lg-6"),
                css_class="row mb-0",
                css_id="row_proceedings",
                style="display: none",
            ),
        )

    def search_results(self):
        """
        Return all public Publication objects fitting search criteria.
        """
        publications = Publication.objects.published()
        if self.acad_field_slug and self.acad_field_slug != "all":
            publications = publications.filter(acad_field__slug=self.acad_field_slug)
            if self.specialty_slug and self.specialty_slug != "all":
                publications = publications.filter(
                    specialties__slug=self.specialty_slug
                )
        if self.cleaned_data.get("author"):
            publications = publications.filter(
                author_list__icontains=self.cleaned_data.get("author")
            )
        if self.cleaned_data.get("title"):
            publications = publications.filter(
                title__icontains=self.cleaned_data.get("title")
            )
        if self.cleaned_data.get("doi_label"):
            publications = publications.filter(
                doi_label__icontains=self.cleaned_data.get("doi_label")
            )
        if self.cleaned_data.get("journal"):
            publications = publications.for_journal(
                self.cleaned_data.get("journal").name
            )
            if self.cleaned_data.get("proceedings"):
                publications = publications.filter(
                    in_issue__proceedings=self.cleaned_data.get("proceedings")
                )
        return publications


class CitationListBibitemsForm(forms.ModelForm):
    latex_bibitems = forms.CharField(widget=forms.Textarea())

    class Meta:
        model = Publication
        fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["latex_bibitems"].widget.attrs.update(
            {"placeholder": "Paste the .tex bibitems here"}
        )

    def extract_dois(self):
        entries_list = self.cleaned_data["latex_bibitems"]
        entries_list = re.sub(r"(?m)^\%.*\n?", "", entries_list)
        entries_list = entries_list.split("\doi{")
        dois = []
        n_entry = 1
        for entry in entries_list[1:]:  # drop first bit before first \doi{
            dois.append(
                {
                    "key": "ref" + str(n_entry),
                    "doi": entry.partition("}")[0],
                }
            )
            n_entry += 1
        return dois

    def save(self, *args, **kwargs):
        self.instance.metadata["citation_list"] = self.extract_dois()
        return super().save(*args, **kwargs)


class AbstractJATSForm(forms.ModelForm):
    abstract_jats = forms.CharField(
        widget=forms.Textarea(
            {
                "placeholder": "Paste the JATS abstract here (use pandoc to generate; see docs)"
            }
        )
    )

    class Meta:
        model = Publication
        fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["abstract_jats"].initial = self.instance.abstract_jats

    def save(self, *args, **kwargs):
        self.instance.abstract_jats = jatsify_tags(self.cleaned_data["abstract_jats"])
        return super().save(*args, **kwargs)


class FundingInfoForm(forms.ModelForm):
    funding_statement = forms.CharField(
        widget=forms.Textarea({"placeholder": "Paste the funding info statement here"})
    )

    class Meta:
        model = Publication
        fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["funding_statement"].initial = self.instance.metadata.get(
            "funding_statement"
        )

    def save(self, *args, **kwargs):
        self.instance.metadata["funding_statement"] = self.cleaned_data[
            "funding_statement"
        ]
        return super().save(*args, **kwargs)


class BasePublicationAuthorsTableFormSet(BaseModelFormSet):
    def save(self, *args, **kwargs):
        objects = super().save(*args, **kwargs)
        for form in self.ordered_forms:
            form.instance.order = form.cleaned_data["ORDER"]
            form.instance.save()
        return objects


PublicationAuthorOrderingFormSet = modelformset_factory(
    PublicationAuthorsTable,
    fields=(),
    can_order=True,
    extra=0,
    formset=BasePublicationAuthorsTableFormSet,
)


class AuthorsTableOrganizationSelectForm(forms.ModelForm):
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="/organizations/organization-autocomplete", attrs={"data-html": True}
        ),
    )

    class Meta:
        model = PublicationAuthorsTable
        fields = []


class CreateMetadataXMLForm(forms.ModelForm):
    schema = None
    parser = None

    @classmethod
    def initialize_lxml(cls):
        if cls.schema is None:
            cls.schema = ET.XMLSchema(
                file=settings.STATIC_ROOT + settings.CROSSREF_SCHEMA_FILE
            )
        if cls.parser is None:
            cls.parser = ET.XMLParser(schema=cls.schema)

    class Meta:
        model = Publication
        fields = ["metadata_xml"]

    def __init__(self, *args, **kwargs):
        xml = self.new_xml(kwargs.get("instance"))
        self.xml_str = self.format_xml(self.decode_html_entities(xml))
        kwargs["initial"] = {"metadata_xml": self.xml_str}

        if self.schema is None or self.parser is None:
            self.initialize_lxml()

        super().__init__(*args, **kwargs)

    @staticmethod
    def decode_html_entities(xml: str):
        # Replace any encoded HTML entities with their decoded counterparts
        for entity, symbol in entitydefs.items():
            if entity in ["lt", "gt", "amp", "quot", "apos"]:
                continue

            xml = xml.replace(f"&{entity};", symbol)

        return xml

    def clean_metadata_xml(self):
        # Flatten the XML before saving
        xml = self.cleaned_data["metadata_xml"]
        xml = re.sub(r"\s*\n+\s*", "", xml, flags=re.MULTILINE)

        return xml

    def save(self, *args, **kwargs):
        self.instance.latest_metadata_update = timezone.now()
        return super().save(*args, **kwargs)

    def new_xml(self, publication):
        """
        Create new XML structure, return as a string.
        """
        # Create a doi_batch_id
        salt = ""
        for i in range(5):
            salt = salt + random.choice(string.ascii_letters)
        salt = salt.encode("utf8")
        idsalt = publication.title[:10]
        idsalt = idsalt.encode("utf8")
        doi_batch_id = hashlib.sha1(salt + idsalt).hexdigest()

        funders = (
            Funder.objects.filter(grants__in=publication.grants.all())
            | publication.funders_generic.all()
        ).distinct()

        # Render from template
        template = loader.get_template("xml/publication_crossref.html")
        context = {
            "domain": get_current_domain(),
            "publication": publication,
            "doi_batch_id": doi_batch_id,
            "deposit_email": settings.CROSSREF_DEPOSIT_EMAIL,
            "funders": funders,
        }
        return template.render(context)

    def format_xml(self, xml_str: str) -> str:
        """
        Format XML by pretty printing it.
        Returns the formatted XML as a string.
        """
        # Try to parse the XML, if it fails, just return the string
        try:
            xml = ET.fromstring(bytes(xml_str, encoding="utf8"))
            xml_str = ET.tostring(xml, pretty_print=True).decode("utf8")
        except:
            pass

        return xml_str

    def validate_xml(self, xml_str: str):
        """
        Validate XML by running it through the schema.
        Returns a tuple of (valid, errors, xml_str).
        """
        # Try to parse the XML, if it fails, just return the string
        try:
            xml_str = self.format_xml(xml_str)
            xml = ET.fromstring(bytes(xml_str, encoding="utf8"))
            valid = self.schema.validate(xml)
            errors = list(self.schema.error_log)
            return valid, errors, xml_str
        except ET.XMLSyntaxError as error:
            return False, [str(error)], xml_str


class CreateMetadataDOAJForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = ["metadata_DOAJ"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        kwargs["initial"] = {"metadata_DOAJ": self.generate(kwargs.get("instance"))}
        super().__init__(*args, **kwargs)

    def generate(self, publication):
        issn = str(publication.get_journal().issn)
        md = {
            "bibjson": {
                "author": [{"name": publication.author_list}],
                "title": publication.title,
                "abstract": publication.abstract,
                "year": publication.publication_date.strftime("%Y"),
                "month": publication.publication_date.strftime("%m"),
                "identifier": [
                    {"type": "eissn", "id": issn},
                    {"type": "doi", "id": publication.doi_string},
                ],
                "link": [
                    {
                        "url": self.request.build_absolute_uri(
                            publication.get_absolute_url()
                        ),
                        "type": "fulltext",
                    }
                ],
                "journal": {
                    "start_page": publication.get_paper_nr(),
                },
            }
        }
        if publication.in_issue:
            if publication.in_issue.in_volume:
                md["bibjson"]["journal"]["volume"] = str(
                    publication.in_issue.in_volume.number
                )
            md["bibjson"]["journal"]["number"] = str(publication.in_issue.number)

        return md


class BaseReferenceFormSet(BaseModelFormSet):
    """
    BaseReferenceFormSet is used to help fill the Reference list for Publications

    It is required to add the required keyword argument `publication` to this FormSet.
    """

    initial_references = []

    def __init__(self, *args, **kwargs):
        self.publication = kwargs.pop("publication")
        extra = kwargs.pop("extra")
        self.extra = int(extra if extra else "0")
        kwargs["form_kwargs"] = {"publication": self.publication}
        super().__init__(*args, **kwargs)

    def prefill(self):
        citations = self.publication.metadata.get("citation_list", [])

        for cite in citations:
            caller = DOICaller(cite["doi"])

            if caller.is_valid:
                # Authors
                author_list = []
                for author in caller._crossref_data["author"][:3]:
                    try:
                        author_list.append(
                            "{}. {}".format(author["given"][0], author["family"])
                        )
                    except KeyError:
                        author_list.append(author["name"])

                if len(author_list) > 2:
                    authors = ", ".join(author_list[:-1])
                    authors += " and " + author_list[-1]
                else:
                    authors = " and ".join(author_list)

                # Citation
                citation = "<em>{}</em> {} <b>{}</b>, {} ({})".format(
                    caller.data["title"],
                    caller.data["journal"],
                    caller.data["volume"],
                    caller.data["pages"],
                    datetime.strptime(caller.data["pub_date"], "%Y-%m-%d").year,
                )

                self.initial_references.append(
                    {
                        "reference_number": cite["key"][3:],
                        "authors": authors,
                        "citation": citation,
                        "identifier": cite["doi"],
                        "link": "https://doi.org/{}".format(cite["doi"]),
                    }
                )
            else:
                self.initial_references.append(
                    {
                        "reference_number": cite["key"][3:],
                        "identifier": cite["doi"],
                        "link": "https://doi.org/{}".format(cite["doi"]),
                    }
                )

        # Add prefill information to the form
        if not self.initial_extra:
            self.initial_extra = self.initial_references
        else:
            self.initial_extra.extend(self.initial_references)
        self.extra += len(self.initial_extra)


class ReferenceForm(forms.ModelForm):
    class Meta:
        model = Reference
        fields = [
            "reference_number",
            "authors",
            "citation",
            "identifier",
            "link",
        ]

    def __init__(self, *args, **kwargs):
        self.publication = kwargs.pop("publication")
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.instance.publication = self.publication
        super().save(*args, **kwargs)


ReferenceFormSet = modelformset_factory(
    Reference, formset=BaseReferenceFormSet, form=ReferenceForm, can_delete=True
)


class DraftPublicationForm(forms.ModelForm):
    """
    This Form is used by the Production Supervisors to create a new Publication object
    and prefill all data. It is only able to create a `draft` version of a Publication object.
    """

    class Meta:
        model = Publication
        fields = [
            "pubtype",
            "doi_label",
            "pdf_file",
            "in_issue",
            "paper_nr",
            "paper_nr_suffix",
            "title",
            "author_list",
            "abstract",
            "acad_field",
            "specialties",
            "approaches",
            "cc_license",
            "submission_date",
            "acceptance_date",
            "publication_date",
        ]

        widgets = {
            "submission_date": forms.DateInput(attrs={"type": "date"}),
            "acceptance_date": forms.DateInput(attrs={"type": "date"}),
            "publication_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(
        self, data=None, identifier_w_vn_nr=None, issue_id=None, *args, **kwargs
    ):
        # Use separate instance to be able to prefill the form without any existing Publication
        self.submission = None
        self.issue = None
        self.to_journal = None
        if identifier_w_vn_nr:
            try:
                self.submission = Submission.objects.accepted().get(
                    preprint__identifier_w_vn_nr=identifier_w_vn_nr
                )
            except Submission.DoesNotExist:
                self.submission = None

        # Check if the Submission is related to a Journal with individual Publications only
        if self.submission:
            try:
                self.to_journal = Journal.objects.has_individual_publications().get(
                    name=self.submission.editorial_decision.for_journal.name
                )
            except Journal.DoesNotExist:
                self.to_journal = None

        # If the Journal is not for individual publications, choose a Issue for Publication
        if issue_id and not self.to_journal:
            try:
                self.issue = self.get_possible_issues().get(id=issue_id)
            except Issue.DoesNotExist:
                self.issue = None

        super().__init__(data, *args, **kwargs)

        if kwargs.get("instance") or self.issue or self.to_journal:
            # When updating: fix in_issue, because many fields are directly related to the issue.
            del self.fields["in_issue"]
            self.prefill_fields()
        else:
            self.fields["in_issue"].queryset = self.get_possible_issues()
            self.delete_secondary_fields()

    def get_possible_issues(self):
        issues = Issue.objects.filter(until_date__gte=timezone.now())
        if self.submission:
            issues = (
                issues.for_journal(self.submission.submitted_to.name)
                | issues.for_journal(
                    self.submission.editorial_decision.for_journal.name
                )
            ).distinct()
        return issues

    def delete_secondary_fields(self):
        """
        Delete fields from the self.fields dictionary. Later on, this submitted sparse form can
        be used to prefill these secondary fields.
        """
        del self.fields["pubtype"]
        del self.fields["doi_label"]
        del self.fields["pdf_file"]
        del self.fields["paper_nr"]
        del self.fields["paper_nr_suffix"]
        del self.fields["title"]
        del self.fields["author_list"]
        del self.fields["abstract"]
        del self.fields["acad_field"]
        del self.fields["specialties"]
        del self.fields["approaches"]
        del self.fields["cc_license"]
        del self.fields["submission_date"]
        del self.fields["acceptance_date"]
        del self.fields["publication_date"]

    def clean(self):
        data = super().clean()
        if not self.instance.id:
            if self.submission:
                self.instance.accepted_submission = self.submission
            if self.issue:
                self.instance.in_issue = self.issue
            if self.to_journal:
                self.instance.in_journal = self.to_journal
        return data

    def save(self, *args, **kwargs):
        """
        Save the Publication object always as a draft and prefill the Publication with
        related Submission data only when appending the Publication.
        """
        do_prefill = False
        if not self.instance.id:
            do_prefill = True
        # Set the cf_citation to empty string to force recalculation
        self.instance.cf_citation = ""
        super().save(*args, **kwargs)
        if do_prefill:
            self.first_time_fill()
        return self.instance

    def first_time_fill(self):
        """
        Take over fields from related Submission object. This can only be done after
        the Publication object has been added to the database due to m2m relations.
        """
        self.instance.status = STATUS_DRAFT

        if self.submission:
            # Copy all existing author and non-author relations to Publication
            for submission_author in self.submission.authors.all():
                PublicationAuthorsTable.objects.create(
                    publication=self.instance, profile=submission_author.profile
                )
            self.instance.topics.add(*self.submission.topics.all())

    def prefill_fields(self):
        if self.submission:
            self.fields["title"].initial = self.submission.title
            self.fields["author_list"].initial = self.submission.author_list
            self.fields["abstract"].initial = self.submission.abstract
            self.fields["acad_field"].initial = self.submission.acad_field.id
            self.fields["specialties"].initial = [
                s.id for s in self.submission.specialties.all()
            ]
            self.fields["approaches"].initial = self.submission.approaches
            self.fields[
                "submission_date"
            ].initial = self.submission.original_submission_date
            self.fields["acceptance_date"].initial = self.submission.acceptance_date
            self.fields["publication_date"].initial = timezone.now()

        # Fill data for Publications grouped by Issues (or Issue+Volume).
        if hasattr(self.instance, "in_issue") and self.instance.in_issue:
            self.issue = self.instance.in_issue
        if self.issue:
            self.prefill_with_issue(self.issue)

        # Fill data for Publications ungrouped; directly linked to a Journal.
        if hasattr(self.instance, "in_journal") and self.instance.in_journal:
            self.to_journal = self.instance.in_issue
        if self.to_journal:
            self.prefill_with_journal(self.to_journal)

    def prefill_with_issue(self, issue):
        # Determine next available paper number:
        if issue.in_volume:
            # Issue/Volume
            paper_nr = (
                Publication.objects.filter(in_issue__in_volume=issue.in_volume).count()
                + 1
            )
        elif issue.in_journal:
            # Issue only
            paper_nr = Publication.objects.filter(in_issue=issue).count() + 1
        if paper_nr > 999:
            raise PaperNumberingError(paper_nr)

        self.fields["paper_nr"].initial = str(paper_nr)
        if issue.in_volume:
            doi_label = "{journal}.{vol}.{issue}.{paper}".format(
                journal=issue.in_volume.in_journal.doi_label,
                vol=issue.in_volume.number,
                issue=issue.number,
                paper=str(paper_nr).rjust(3, "0"),
            )
        elif issue.in_journal:
            doi_label = "{journal}.{issue}.{paper}".format(
                journal=issue.in_journal.doi_label,
                issue=issue.number,
                paper=str(paper_nr).rjust(3, "0"),
            )
        self.fields["doi_label"].initial = doi_label
        doi_string = "10.21468/{doi}".format(doi=doi_label)

    def prefill_with_journal(self, journal):
        # Determine next available paper number:
        # paper_nr = journal.publications.count() + 1
        paper_nr = (
            journal.publications.aggregate(Max("paper_nr"))["paper_nr__max"] or 0
        ) + 1
        self.fields["paper_nr"].initial = str(paper_nr)
        doi_label = "{journal}.{paper}".format(
            journal=journal.doi_label, paper=paper_nr
        )
        self.fields["doi_label"].initial = doi_label


class DraftAccompanyingPublicationForm(forms.Form):
    anchor = forms.ModelChoiceField(
        queryset=Publication.objects.all(),
        widget=forms.HiddenInput(),
    )
    title = forms.CharField(max_length=300)
    abstract = forms.CharField(widget=forms.Textarea())
    doi_label_suffix = forms.CharField(max_length=128)
    pubtype = forms.ChoiceField(
        choices=Publication.PUBTYPE_CHOICES,
        widget=forms.RadioSelect(),
        label="Publication type",
    )
    inherit = forms.MultipleChoiceField(
        choices=[
            ("abstract_jats", "Abstract (JATS)"),
            ("metadata.funding_statement", "Funding statement"),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={"checked": "checked"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("anchor", css_class="mb-3"),
            Field("pubtype", css_class="d-flex flex-wrap gap-3 mb-3"),
            Field("title", css_class="mb-3"),
            Field("abstract", css_class="mb-3"),
            Field("doi_label_suffix", css_class="mb-3"),
            Field(
                "inherit",
                css_class="d-flex flex-wrap gap-2 mb-3",
            ),
            ButtonHolder(Submit("submit", "Submit", css_class="btn btn-primary")),
        )

    def save(self, *args, **kwargs):
        anchor = self.cleaned_data["anchor"]
        # Create a new Publication based on the anchor data
        companion = Publication(
            accepted_submission=anchor.accepted_submission,
            in_issue=anchor.in_issue,
            in_journal=anchor.in_journal,
            paper_nr=anchor.paper_nr,
            paper_nr_suffix=self.cleaned_data["doi_label_suffix"],
            status=STATUS_DRAFT,
            title=self.cleaned_data["title"],
            author_list=anchor.author_list,
            abstract=self.cleaned_data["abstract"],
            acad_field=anchor.acad_field,
            approaches=anchor.approaches,
            doi_label=f"{anchor.doi_label}-{self.cleaned_data['doi_label_suffix']}",
            submission_date=anchor.submission_date,
            acceptance_date=anchor.acceptance_date,
            publication_date=anchor.publication_date,
            pubtype=self.cleaned_data["pubtype"],
        )
        companion.save()
        # Handle ManyToMany fields
        companion.specialties.add(*anchor.specialties.all())
        companion.topics.add(*anchor.topics.all())
        companion.grants.add(*anchor.grants.all())
        companion.funders_generic.add(*anchor.funders_generic.all())

        # Add authors, using anchor info
        for author in anchor.authors.all():
            pat = PublicationAuthorsTable.objects.create(
                publication=companion,
                profile=author.profile,
                order=author.order,
            )
            pat.affiliations.add(*author.affiliations.all())

        # Add References, using anchor info
        for reference in anchor.references.all():
            Reference.objects.create(
                reference_number=reference.reference_number,
                publication=companion,
                authors=reference.authors,
                citation=reference.citation,
                identifier=reference.identifier,
                link=reference.link,
            )

        # Add PubFracs
        for pubfrac in anchor.pubfracs.all():
            PubFrac.objects.create(
                organization=pubfrac.organization,
                publication=companion,
                fraction=pubfrac.fraction,
            )

        # Add DOI of each companion to the anchor's metadata and vice versa
        anchor.metadata["citation_list"].append(
            {
                "doi": companion.doi_string,
                "key": "ref" + str(len(anchor.metadata["citation_list"]) + 1),
            }
        )
        anchor.save()

        companion.metadata.setdefault("citation_list", [])
        companion.metadata["citation_list"].append(
            {
                "doi": anchor.doi_string,
                "key": "ref" + str(len(companion.metadata["citation_list"]) + 1),
            }
        )

        # Inherit the selected fields from the anchor
        for field in self.cleaned_data["inherit"]:
            if "." not in field:
                setattr(companion, field, getattr(anchor, field))
            # Inherit the selected fields from the anchor's field as a dict
            else:
                field, key = field.split(".")
                field_dict = getattr(companion, field)
                field_dict[key] = getattr(anchor, field).get(key)
                setattr(companion, field, field_dict)

        companion.save()

        return companion


class DraftPublicationUpdateForm(forms.ModelForm):
    class Meta:
        model = PublicationUpdate
        fields = [
            "publication",
            "update_type",
            "text",
            "number",
            "publication_date",
            "doi_label",
        ]
        widgets = {
            "publication": forms.HiddenInput(),
            "number": forms.HiddenInput(),
            "text": forms.Textarea(
                attrs={"placeholder": "Describe the changes made to the publication."}
            ),
            "publication_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        publication = kwargs.pop("publication", None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("publication", css_class="mb-3"),
            Field("number", css_class="mb-3"),
            Field("update_type", css_class="mb-3"),
            Field("publication_date", css_class="mb-3"),
            Field("text", css_class="mb-3"),
            ButtonHolder(Submit("submit", "Submit", css_class="btn btn-primary")),
        )

        self.initial["publication"] = publication
        self.initial["doi_label"] = publication.doi_label
        self.initial["number"] = publication.updates.count() + 1
        self.initial["publication_date"] = timezone.now()


class DraftPublicationApprovalForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = ()

    def save(self, commit=True):
        self.instance.status = PUBLICATION_PREPUBLISHED
        if commit:
            self.instance.save()
            mail_sender = DirectMailUtil("publication_ready", instance=self.instance)
            mail_sender.send_mail()
        return self.instance


class PublicationGrantsForm(forms.ModelForm):
    grant = forms.ModelChoiceField(queryset=Grant.objects.none())

    class Meta:
        model = Publication
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["grant"].queryset = Grant.objects.exclude(
            id__in=self.instance.grants.values_list("id", flat=True)
        )

    def save(self, commit=True):
        if commit:
            self.instance.grants.add(self.cleaned_data["grant"])
        return self.instance


class PublicationPublishForm(RequestFormMixin, forms.ModelForm):
    class Meta:
        model = Publication
        fields = []

    def move_pdf(self):
        """
        To keep the Publication pdfs organized we move the pdfs to their own folder
        organized by journal and optional issue folder.
        """
        if self.instance.pdf_file:
            initial_path = self.instance.pdf_file.path
            new_dir = ""
            if self.instance.in_issue:
                new_dir += self.instance.in_issue.path
            elif self.instance.in_journal:
                new_dir += "SCIPOST_JOURNALS/{name}".format(
                    name=self.instance.in_journal.doi_label
                )
            new_dir += "/{paper_nr}".format(paper_nr=self.instance.get_paper_nr())
            os.makedirs(settings.MEDIA_ROOT + new_dir, exist_ok=True)
            new_dir += "/{doi}.pdf".format(
                doi=self.instance.doi_label.replace(".", "_")
            )
            os.rename(initial_path, settings.MEDIA_ROOT + new_dir)
            self.instance.pdf_file.name = new_dir

        self.instance.status = PUBLICATION_PUBLISHED
        self.instance.save()

    def update_submission(self):
        # Mark the submission as having been published:
        submission = self.instance.accepted_submission
        submission.published_as = self.instance
        submission.status = submission.PUBLISHED
        submission.save()

        # Add SubmissionEvents
        submission.add_general_event(
            "The Submission has been published as %s." % self.instance.doi_label
        )

    def update_stream(self):
        # Update ProductionStream
        submission = self.instance.accepted_submission
        if hasattr(submission, "production_stream"):
            stream = submission.production_stream
            # WARNING: We don't need the "published" stream status
            # so long as we don't use invitation officers.
            # If we reinstate this, we need to revert the status to published.
            stream.status = PRODUCTION_STREAM_COMPLETED
            stream.save()
            if self.request.user.production_user:
                prodevent = ProductionEvent(
                    stream=stream,
                    event="status",
                    comments=" published the manuscript.",
                    noted_by=self.request.user.production_user,
                )
                prodevent.save()

    def save(self, commit=True):
        if commit:
            self.move_pdf()
            self.update_submission()
            self.update_stream()

            # Email authors
            JournalUtils.load({"publication": self.instance})
            JournalUtils.send_authors_paper_published_email()

        return self.instance


class VolumeForm(forms.ModelForm):
    """
    Add or Update a Volume instance which is directly related to either a Journal.
    """

    class Meta:
        model = Volume
        fields = (
            "in_journal",
            "start_date",
            "until_date",
            "doi_label",
        )
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "until_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.id:
            del self.fields["doi_label"]

    def save(self):
        if self.instance.id:
            # Use regular save method if updating existing instance.
            return super().save()

        # Obtain next number, path and DOI if creating new Issue.
        volume = super().save(commit=False)
        volume.number = volume.in_journal.volumes.count() + 1
        volume.doi_label = "{}.{}".format(volume.in_journal.doi_label, volume.number)
        volume.save()
        return volume


class IssueForm(forms.ModelForm):
    """
    Add or Update an Issue instance which is directly related to either a Journal or a Volume.
    """

    class Meta:
        model = Issue
        fields = (
            "in_journal",
            "in_volume",
            "start_date",
            "until_date",
            "status",
            "doi_label",
        )
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "until_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.id:
            del self.fields["doi_label"]

    def save(self):
        if self.instance.id:
            # Use regular save method if updating existing instance.
            return super().save()

        # Obtain next number, path and DOI if creating new Issue.
        issue = super().save(commit=False)
        journal = issue.get_journal()
        path = settings.JOURNALS_DIR
        if journal.has_volumes:
            volume = journal.volumes.first()
            number = volume.issues.count() + 1
            doi = "{}.{}.{}".format(journal.doi_label, volume.number, number)
            path += "/{}/{}/{}".format(journal.doi_label, volume.number, number)
        else:
            if self.cleaned_data["status"] == STATUS_PUBLICLY_OPEN:
                # Temporary park this issue with a number generated from the timestamp
                # This is useful for e.g. Proceedings, which only get their final
                # number when published (not when they are made publicly open for submission).
                # The format is [YYYY][MM][3-digit code]
                # where the next-available 3-digit code is found
                number_check = 1000 * int(timezone.now().strftime("%Y%m"))
                number = (
                    number_check
                    + journal.issues.filter(number__gt=number_check).count()
                    + 1
                )
            else:
                number = journal.issues.count() + 1
            volume = None
            doi = "{}.{}".format(journal.doi_label, number)
            path += "/{}/{}".format(journal.doi_label, number)
        issue.number = number
        issue.slug = str(number)
        issue.doi_label = doi
        issue.path = path
        issue.save()
        return issue


class SetPubFracForm(forms.ModelForm):
    class Meta:
        model = PubFrac
        fields = ["organization", "publication", "fraction"]

    def __init__(self, *args, **kwargs):
        super(SetPubFracForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            self.fields["organization"].disabled = True
            self.fields["publication"].widget = forms.HiddenInput()


class BasePubFracsFormSet(BaseModelFormSet):
    def clean(self):
        """
        Checks that the fractions add up to one.
        """
        norm = 0
        for form in self.forms:
            form.is_valid()
            norm += 1000 * form.cleaned_data.get("fraction", 0)
        if norm != 1000:
            raise forms.ValidationError(
                f"The fractions do not add up to one! Getting {norm} / 1000"
            )


PubFracsFormSet = modelformset_factory(
    PubFrac,
    fields=("publication", "organization", "fraction"),
    formset=BasePubFracsFormSet,
    form=SetPubFracForm,
    extra=0,
)


class PublicationDynSelForm(forms.Form):
    q = forms.CharField(max_length=32, label="Search (by title, author names)")
    action_url_name = forms.CharField()
    action_url_base_kwargs = forms.JSONField(required=False)
    action_target_element_id = forms.CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            FloatingField("q", autocomplete="off"),
            Field("action_url_name", type="hidden"),
            Field("action_url_base_kwargs", type="hidden"),
            Field("action_target_element_id", type="hidden"),
        )

    def search_results(self):
        if self.cleaned_data["q"]:
            publications = Publication.objects.filter(
                Q(title__icontains=self.cleaned_data["q"])
                | Q(author_list__icontains=self.cleaned_data["q"])
                | Q(doi_label__icontains=self.cleaned_data["q"])
            ).distinct()
            return publications
        else:
            return Publication.objects.none()


class HTMXInlinePublicationResourceForm(HTMXInlineCRUDModelForm):
    class Meta:
        model = PublicationResource
        fields = ["publication", "_type", "url", "comments"]
        widgets = {
            "publication": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        doi = kwargs.pop("doi_label", None)
        super().__init__(*args, **kwargs)
        self.fields["_type"].choices = PublicationResource.TYPE_CHOICES
        self.fields["_type"].label = "Resource type"
        self.fields["url"].label = "URL"

        if doi:
            self.fields["publication"].initial = Publication.objects.get(doi_label=doi)

        self.helper.layout = Layout(
            Div(FloatingField("publication"), css_class="col-12"),
            Div(FloatingField("_type"), css_class="col-3"),
            Div(FloatingField("url"), css_class="col-9"),
            Div(FloatingField("comments"), css_class="col"),
        )
