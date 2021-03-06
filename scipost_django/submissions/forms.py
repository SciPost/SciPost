__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django import forms
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.forms.formsets import ORDERING_FIELD_NAME
from django.utils import timezone

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Fieldset, ButtonHolder, Submit
from crispy_forms.bootstrap import InlineRadios
from crispy_bootstrap5.bootstrap5 import FloatingField

from dal import autocomplete

from .constants import (
    ASSIGNMENT_BOOL,
    ASSIGNMENT_REFUSAL_REASONS,
    STATUS_RESUBMITTED,
    REPORT_ACTION_CHOICES,
    REPORT_REFUSAL_CHOICES,
    STATUS_REJECTED,
    STATUS_INCOMING,
    REPORT_POST_EDREC,
    REPORT_NORMAL,
    STATUS_DRAFT,
    STATUS_UNVETTED,
    REPORT_ACTION_ACCEPT,
    REPORT_ACTION_REFUSE,
    STATUS_UNASSIGNED,
    SUBMISSION_STATUS,
    STATUS_ASSIGNMENT_FAILED,
    STATUS_ACCEPTED_AWAITING_PUBOFFER_ACCEPTANCE,
    STATUS_PUBLISHED,
    PUT_TO_VOTING,
    SUBMISSION_CYCLE_CHOICES,
    CYCLE_UNDETERMINED,
    CYCLE_DEFAULT,
    CYCLE_SHORT,
    CYCLE_DIRECT_REC,
    EIC_REC_PUBLISH,
    EIC_REC_MINOR_REVISION,
    EIC_REC_MAJOR_REVISION,
    EIC_REC_REJECT,
    ALT_REC_CHOICES,
    SUBMISSION_TIERS,
    STATUS_VETTED,
    DECISION_FIXED,
    DEPRECATED,
    STATUS_COMPLETED,
    STATUS_EIC_ASSIGNED,
    STATUS_PREASSIGNED,
    STATUS_REPLACED,
    STATUS_FAILED_PRESCREENING,
    STATUS_DEPRECATED,
    STATUS_ACCEPTED,
    STATUS_DECLINED,
    STATUS_WITHDRAWN,
)
from . import exceptions, helpers
from .helpers import to_ascii_only
from .models import (
    PreprintServer,
    Submission,
    RefereeInvitation,
    Report,
    EICRecommendation,
    EditorialAssignment,
    SubmissionTiering,
    EditorialDecision,
    iThenticateReport,
    EditorialCommunication,
)
from .regexes import CHEMRXIV_DOI_PATTERN

from colleges.models import Fellowship
from common.utils import Q_with_alternative_spellings
from journals.models import Journal
from mails.utils import DirectMailUtil
from ontology.models import AcademicField, Specialty
from preprints.helpers import get_new_scipost_identifier
from preprints.models import Preprint
from proceedings.models import Proceedings
from profiles.models import Profile
from scipost.services import DOICaller, ArxivCaller, FigshareCaller, OSFPreprintsCaller
from scipost.models import Contributor, Remark
import strings

import iThenticate

ARXIV_IDENTIFIER_PATTERN_NEW = r"^[0-9]{4,}\.[0-9]{4,5}v[0-9]{1,2}$"
FIGSHARE_IDENTIFIER_PATTERN = r"^[0-9]+\.v[0-9]{1,2}$"
OSFPREPRINTS_IDENTIFIER_PATTERN = r"^[a-z0-9]+$"


class SubmissionSearchForm(forms.Form):
    author = forms.CharField(max_length=100, required=False, label="Author(s)")
    title = forms.CharField(max_length=100, required=False)
    submitted_to = forms.ModelChoiceField(
        queryset=Journal.objects.active(), required=False
    )
    identifier = forms.CharField(max_length=128, required=False)
    proceedings = forms.ModelChoiceField(
        queryset=Proceedings.objects.order_by("-submissions_close"), required=False
    )

    def __init__(self, *args, **kwargs):
        self.acad_field_slug = kwargs.pop("acad_field_slug")
        self.specialty_slug = kwargs.pop("specialty_slug")
        self.reports_needed = kwargs.pop("reports_needed")
        super().__init__(*args, **kwargs)
        if self.acad_field_slug:
            self.fields["submitted_to"].queryset = Journal.objects.filter(
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
                Div(FloatingField("submitted_to"), css_class="col-lg-6"),
                Div(FloatingField("identifier"), css_class="col-lg-6"),
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
        Return all Submission objects fitting search criteria.
        """
        submissions = Submission.objects.public_newest().unpublished()
        if self.acad_field_slug and self.acad_field_slug != "all":
            submissions = submissions.filter(acad_field__slug=self.acad_field_slug)
            if self.specialty_slug and self.specialty_slug != "all":
                submissions = submissions.filter(specialties__slug=self.specialty_slug)
        if self.cleaned_data.get("submitted_to"):
            submissions = submissions.filter(
                submitted_to=self.cleaned_data.get("submitted_to")
            )
        if self.cleaned_data.get("proceedings"):
            submissions = submissions.filter(
                proceedings=self.cleaned_data.get("proceedings")
            )
        if self.cleaned_data.get("author"):
            submissions = submissions.filter(
                author_list__icontains=self.cleaned_data.get("author")
            )
        if self.cleaned_data.get("title"):
            submissions = submissions.filter(
                title__icontains=self.cleaned_data.get("title")
            )
        if self.cleaned_data.get("identifier"):
            submissions = submissions.filter(
                preprint__identifier_w_vn_nr__icontains=self.cleaned_data.get(
                    "identifier"
                )
            )
        if self.reports_needed:
            submissions = (
                submissions.actively_refereeing()
                .open_for_reporting()
                .reports_needed()
                .order_by("submission_date")
            )
        return submissions


class SubmissionPoolSearchForm(forms.Form):
    """Filter a Submission queryset using basic search fields."""

    submitted_to = forms.ModelChoiceField(
        queryset=Journal.objects.active(), required=False
    )
    specialties = forms.ModelMultipleChoiceField(
        queryset=Specialty.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url="/ontology/specialty-autocomplete", attrs={"data-html": True}
        ),
        label="Specialties",
        required=False,
    )
    proceedings = forms.ModelChoiceField(
        queryset=Proceedings.objects.order_by("-submissions_close"), required=False
    )
    author = forms.CharField(max_length=100, required=False, label="Author(s)")
    title = forms.CharField(max_length=100, required=False)
    identifier = forms.CharField(max_length=128, required=False)
    status = forms.ChoiceField(
        choices=(
            ("All", (("all", "All Submissions"),)),
            (
                "Pre-screening",
                (
                    (STATUS_INCOMING, "In pre-screening"),
                    (STATUS_FAILED_PRESCREENING, "Failed pre-screening"),
                ),
            ),
            (
                "Screening",
                (
                    (STATUS_UNASSIGNED, "Unassigned, awaiting editor assignment"),
                    ("unassigned_1", "... unassigned for > 1 week"),
                    ("unassigned_2", "... unassigned for > 2 weeks"),
                    ("unassigned_4", "... unassigned for > 4 weeks"),
                    (
                        STATUS_ASSIGNMENT_FAILED,
                        "Failed to assign Editor-in-charge; manuscript rejected",
                    ),
                ),
            ),
            (
                "Refereeing",
                (
                    ("actively_refereeing", "In refereeing"),
                    ("unvetted_reports", "... with unvetted Reports"),
                    ("deadline_passed", "deadline passed, no recommendation yet"),
                    ("refereeing_1", "Refereeing round ongoing for > 1 month"),
                    ("refereeing_2", "Refereeing round ongoing for > 2 months"),
                    ("refereeing_3", "Refereeing round ongoing for > 3 months"),
                ),
            ),
            (
                "Revision requested",
                (
                    ("revision_requested", "Minor or major revision requested"),
                ),
            ),
            (
                "Voting",
                (
                    ("voting_prepare", "Voting in preparation"),
                    ("voting_ongoing", "Voting ongoing"),
                    ("voting_1", "... in voting for > 1 week"),
                    ("voting_2", "... in voting for > 2 weeks"),
                    ("voting_4", "... in voting for > 4 weeks"),
                ),
            ),
            (
                "Decided",
                (
                    (STATUS_ACCEPTED, "Accepted"),
                    (
                        STATUS_ACCEPTED_AWAITING_PUBOFFER_ACCEPTANCE,
                        "Accepted in other journal; awaiting puboffer acceptance",
                    ),
                    (STATUS_REJECTED, "Rejected"),
                    (STATUS_WITHDRAWN, "Withdrawn by the Authors"),
                ),
            ),
            ("Processed", ((STATUS_PUBLISHED, "Published"),)),
        ),
    )
    editor_in_charge = forms.ModelChoiceField(
        queryset=Fellowship.objects.active(), required=False
    )
    search_set = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=(
            ("eic", "I am Editor-in-charge"),
            ("current", "All currently in processing"),
            ("historical", "All accessible history"),
        ),
        initial="current",
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        if not user.contributor.is_ed_admin:
            # restrict journals to those of Colleges of user's Fellowships
            college_id_list = [
                f.college.id for f in user.contributor.fellowships.active()
            ]
            self.fields["submitted_to"].queryset = Journal.objects.filter(
                college__in=college_id_list
            )
        if user.contributor.is_ed_admin:
            # Remove 'I am Editor-in-charge' choice
            self.fields["search_set"].choices = (
                ("current", "All currently in processing"),
                ("historical", "All accessible history"),
            )
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(FloatingField("submitted_to"), css_class="col-lg-6"),
                Div(FloatingField("specialties"), css_class="col-lg-6"),
                css_class="row mb-0",
            ),
            Div(
                Div(FloatingField("proceedings"), css_class="col-lg-6"),
                css_class="row mb-0",
                css_id="row_proceedings",
                style="display: none",
            ),
            Div(
                Div(FloatingField("author"), css_class="col-lg-6"),
                Div(FloatingField("title"), css_class="col-lg-6"),
                css_class="row mb-0",
            ),
            Div(
                Div(FloatingField("identifier"), css_class="col-lg-3"),
                Div(FloatingField("status"), css_class="col-lg-5"),
                Div(
                    FloatingField("editor_in_charge"),
                    css_class="col-lg-4",
                    css_id="col_eic",
                ),
                css_class="row mb-0",
            ),
            Div(Div(InlineRadios("search_set"), css_class="col"), css_class="row mb-0"),
        )

    def search_results(self, user):
        """
        Return all Submission objects fitting search criteria.
        """
        if self.cleaned_data.get("search_set") == "eic":
            submissions = Submission.objects.filter_for_eic(user)
        elif self.cleaned_data.get("search_set") == "current":
            submissions = Submission.objects.pool(user)
        else:  # include historical items
            submissions = Submission.objects.pool_editable(user)
        if self.cleaned_data.get("specialties"):
            submissions = submissions.filter(
                specialties__in=self.cleaned_data.get("specialties")
            )
        if self.cleaned_data.get("submitted_to"):
            submissions = submissions.filter(
                submitted_to=self.cleaned_data.get("submitted_to")
            )
        if self.cleaned_data.get("proceedings"):
            submissions = submissions.filter(
                proceedings=self.cleaned_data.get("proceedings")
            )
        if self.cleaned_data.get("author"):
            submissions = submissions.filter(
                author_list__icontains=self.cleaned_data.get("author")
            )
        if self.cleaned_data.get("title"):
            submissions = submissions.filter(
                title__icontains=self.cleaned_data.get("title")
            )
        if self.cleaned_data.get("identifier"):
            submissions = submissions.filter(
                preprint__identifier_w_vn_nr__icontains=self.cleaned_data.get(
                    "identifier"
                )
            )

        # filter by status
        status = self.cleaned_data.get("status")
        if status == "all":
            pass
        elif status == "unassigned_1":
            submissions = submissions.filter(
                status=STATUS_UNASSIGNED,
                submission_date__lt=timezone.now() - datetime.timedelta(days=7),
            )
        elif status == "unassigned_2":
            submissions = submissions.filter(
                status=STATUS_UNASSIGNED,
                submission_date__lt=timezone.now() - datetime.timedelta(days=14),
            )
        elif status == "unassigned_4":
            submissions = submissions.filter(
                status=STATUS_UNASSIGNED,
                submission_date__lt=timezone.now() - datetime.timedelta(days=28),
            )
        elif status == "actively_refereeing":
            submissions = submissions.actively_refereeing()
        elif status == "unvetted_reports":
            reports_to_vet = Report.objects.awaiting_vetting()
            id_list = [r.submission.id for r in reports_to_vet.all()]
            submissions = submissions.filter(id__in=id_list)
        elif status == "deadline_passed":
            submissions = submissions.actively_refereeing().filter(
                reporting_deadline__lt=timezone.now(),
            ).exclude(eicrecommendations__isnull=False)
        elif status == "refereeing_1":
            submissions = submissions.filter(
                referee_invitations__date_invited__lt=(
                    timezone.now() - datetime.timedelta(days=30)
                )
            ).exclude(
                referee_invitations__date_invited__lt=(
                    timezone.now() - datetime.timedelta(days=60)
                )
            ).distinct().exclude(eicrecommendations__isnull=False)
        elif status == "refereeing_2":
            submissions = submissions.filter(
                referee_invitations__date_invited__lt=(
                    timezone.now() - datetime.timedelta(days=60)
                )
            ).exclude(
                referee_invitations__date_invited__lt=(
                    timezone.now() - datetime.timedelta(days=90)
                )
            ).distinct().exclude(eicrecommendations__isnull=False)
        elif status == "refereeing_3":
            submissions = submissions.filter(
                referee_invitations__date_invited__lt=(
                    timezone.now() - datetime.timedelta(days=90)
                )
            ).distinct().exclude(eicrecommendations__isnull=False)
        elif status == "revision_requested":
            submissions = submissions.revision_requested()
        elif status == "voting_prepare":
            submissions = submissions.voting_in_preparation()
        elif status == "voting_ongoing":
            submissions = submissions.undergoing_voting()
        elif status == "voting_1":
            submissions = submissions.undergoing_voting(longer_than_days=7)
        elif status == "voting_2":
            submissions = submissions.undergoing_voting(longer_than_days=14)
        elif status == "voting_4":
            submissions = submissions.undergoing_voting(longer_than_days=28)
        else:
            submissions = submissions.filter(status=status)

        # filter by EIC
        if self.cleaned_data.get("editor_in_charge"):
            submissions = submissions.filter(
                editor_in_charge=self.cleaned_data.get("editor_in_charge").contributor
            )
        return submissions


class ReportSearchForm(forms.Form):
    submission_title = forms.CharField(max_length=100, required=False)

    def __init__(self, *args, **kwargs):
        self.acad_field_slug = kwargs.pop("acad_field_slug")
        self.specialty_slug = kwargs.pop("specialty_slug")
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(FloatingField("submission_title"), css_class="col-lg-6"),
            ),
        )

    def search_results(self):
        reports = Report.objects.accepted()
        if self.acad_field_slug and self.acad_field_slug != "all":
            reports = reports.filter(submission__acad_field__slug=self.acad_field_slug)
            if self.specialty_slug and self.specialty_slug != "all":
                reports = reports.filter(
                    submission__specialties__slug=self.specialty_slug
                )
        if self.cleaned_data.get("submission_title"):
            reports = reports.filter(
                submission__title__icontains=self.cleaned_data.get("submission_title")
            )
        return reports


# Marked for deprecation
class SubmissionOldSearchForm(forms.Form):
    """Filter a Submission queryset using basic search fields."""

    author = forms.CharField(max_length=100, required=False, label="Author(s)")
    title = forms.CharField(max_length=100, required=False)
    abstract = forms.CharField(max_length=1000, required=False)

    def search_results(self):
        """Return all Submission objects according to search."""
        return Submission.objects.public_newest().filter(
            title__icontains=self.cleaned_data.get("title", ""),
            author_list__icontains=self.cleaned_data.get("author", ""),
            abstract__icontains=self.cleaned_data.get("abstract", ""),
        )



######################################################################
#
# SubmissionForm prefill facilities. One class per integrated server.
#
######################################################################

# Checks


def check_resubmission_readiness(requested_by, submission):
    """
    Check if submission can be resubmitted.
    """
    if submission:
        if submission.status == STATUS_REJECTED:
            # Explicitly give rejected status warning.
            error_message = (
                "This preprint has previously undergone refereeing "
                "and has been rejected. Resubmission is only possible "
                "if the manuscript has been substantially reworked into "
                "a new submission with distinct identifier."
            )
            raise forms.ValidationError(error_message)
        elif submission.open_for_resubmission:
            # Check if verified author list contains current user.
            if requested_by.contributor not in submission.authors.all():
                error_message = (
                    "There exists a preprint with this identifier "
                    "but an earlier version number. Resubmission is only possible"
                    " if you are a registered author of this manuscript."
                )
                raise forms.ValidationError(error_message)
        else:
            # Submission has an inappropriate status for resubmission.
            error_message = (
                "There exists a preprint with this identifier "
                "but an earlier version number, which is still undergoing "
                "peer refereeing. "
                "A resubmission can only be performed after request "
                "from the Editor-in-charge. Please wait until the "
                "closing of the previous refereeing round and "
                "formulation of the Editorial Recommendation "
                "before proceeding with a resubmission."
            )
            raise forms.ValidationError(error_message)


def check_identifier_is_unused(identifier):
    # Check if identifier has already been used for submission
    if Submission.objects.filter(preprint__identifier_w_vn_nr=identifier).exists():
        error_message = "This preprint version has already been submitted to SciPost."
        raise forms.ValidationError(error_message, code="duplicate")


def check_arxiv_identifier_w_vn_nr(identifier):
    caller = ArxivCaller(identifier)
    if caller.is_valid:
        arxiv_data = caller.data
        metadata = caller.metadata
    else:
        error_message = "A preprint associated to this identifier does not exist."
        raise forms.ValidationError(error_message)

    # Check if this paper has already been published (according to arXiv)
    published_id = None
    if "arxiv_doi" in arxiv_data:
        published_id = arxiv_data["arxiv_doi"]
    elif "arxiv_journal_ref" in arxiv_data:
        published_id = arxiv_data["arxiv_journal_ref"]

    if published_id:
        error_message = (
            "This paper has been published under DOI %(published_id)s. "
            "It cannot be submitted again."
        )
        raise forms.ValidationError(
            error_message, code="published", params={"published_id": published_id}
        )
    return arxiv_data, metadata, identifier


def check_chemrxiv_doi(doi):
    """
    Call Crossref to get ChemRxiv preprint data.
    """
    caller = DOICaller(doi)
    if caller.is_valid:
        data = caller.data
        metadata = caller.data["crossref_data"]
    else:
        error_message = "A preprint associated to this DOI does not exist."
        raise forms.ValidationError(error_message)

    # Check if the type of this resource is indeed a preprint
    if "subtype" in metadata:
        if metadata["subtype"] != "preprint":
            error_message = (
                "This does not seem to be a preprint: the type "
                "returned by Crossref on behalf of "
                "%(preprint_server) is %(subtype). "
                "Please contact techsupport."
            )
            raise forms.ValidationError(
                error_message,
                code="wrong_subtype",
                params={
                    "preprint_server": preprint_server.name,
                    "subtype": metadata["subtype"],
                },
            )
    else:
        raise forms.ValidationError(
            "Crossref failed to return a subtype. Please contact techsupport.",
            code="wrong_subtype",
        )

    # Explicitly add ChemRxiv as the preprint server:
    data["preprint_server"] = PreprintServer.objects.get(name="ChemRxiv")
    data["preprint_link"] = "https://doi.org/%s" % doi
    # Build the identifier by stripping the DOI prefix:
    identifier = doi
    data["identifier_w_vn_nr"] = identifier
    return data, metadata, identifier


def check_figshare_identifier_w_vn_nr(preprint_server, figshare_identifier_w_vn_nr):
    """
    Call Figshare to retrieve submission prefill data and perform basic checks.

    This method is defined outside of FigsharePrefillform in order to
    also be callable by SubmissionForm.
    """
    caller = FigshareCaller(preprint_server, figshare_identifier_w_vn_nr)
    if caller.is_valid:
        figshare_data = caller.data
        metadata = caller.metadata
    else:
        error_message = "A preprint associated to this identifier does not exist."
        raise forms.ValidationError(error_message)

    # Check if the type of this resource is indeed a preprint
    if "defined_type_name" in metadata:
        if metadata["defined_type_name"] != "preprint":
            error_message = (
                "This does not seem to be a preprint: the type "
                "returned by Figshare on behalf of "
                "%(preprint_server) is %(defined_type_name)s. "
                "Please contact techsupport."
            )
            raise forms.ValidationError(
                error_message,
                code="wrong_defined_type_name",
                params={
                    "preprint_server": preprint_server.name,
                    "defined_type_name": metadata["defined_type_name"],
                },
            )
    else:
        raise forms.ValidationError(
            "Figshare failed to return a defined_type_name. Please contact techsupport.",
            code="wrong_defined_type_name",
        )

    # Check if this article has already been published (according to Figshare)
    published_id = None
    if "resource_doi" in metadata:
        published_id = metadata["resource_doi"]

    if published_id:
        error_message = (
            "This paper has been published under DOI %(published_id)s. "
            "It cannot be submitted again."
        )
        raise forms.ValidationError(
            error_message, code="published", params={"published_id": published_id}
        )
    identifier = preprint_server.name.lower() + "_" + figshare_identifier_w_vn_nr
    return figshare_data, metadata, identifier


# DEPRECATED
def check_chemrxiv_figshare_identifier_w_vn_nr(chemrxiv_identifier_w_vn_nr):
    """
    Call `check_figshare_identifier_w_vn_nr` but correct identifier
    by substituting `chemrxiv` for `figshare`.
    """
    data, metadata, identifier = check_figshare_identifier_w_vn_nr(
        PreprintServer.objects.get(name="ChemRxiv"), chemrxiv_identifier_w_vn_nr
    )
    return data, metadata, identifier.replace("figshare", "chemrxiv")


def check_techrxiv_identifier_w_vn_nr(techrxiv_identifier_w_vn_nr):
    """
    Call `check_figshare_identifier_w_vn_nr` but correct identifier
    by substituting `techrxiv` for `figshare`.
    """
    data, metadata, identifier = check_figshare_identifier_w_vn_nr(
        PreprintServer.objects.get(name="TechRxiv"), techrxiv_identifier_w_vn_nr
    )
    return data, metadata, identifier.replace("figshare", "techrxiv")


def check_advance_identifier_w_vn_nr(advance_identifier_w_vn_nr):
    """
    Call `check_figshare_identifier_w_vn_nr` but correct identifier
    by substituting `advance` for `figshare`.
    """
    data, metadata, identifier = check_figshare_identifier_w_vn_nr(
        PreprintServer.objects.get(name="Advance"), advance_identifier_w_vn_nr
    )
    return data, metadata, identifier.replace("figshare", "advance")


def check_osfpreprints_identifier(preprint_server, osfpreprints_identifier):
    """
    Call OSFPreprints to retrieve submission prefill data and perform basic checks.

    This method is defined outside of FigsharePrefillform in order to
    also be callable by SubmissionForm.
    """
    caller = OSFPreprintsCaller(preprint_server, osfpreprints_identifier)
    if caller.is_valid:
        osfpreprints_data = caller.data
        metadata = caller.metadata
    else:
        error_message = "A preprint associated to this identifier does not exist."
        raise forms.ValidationError(error_message)

    # Check if the type of this resource is indeed a preprint
    if "type" in metadata:
        if metadata["type"] != "preprints":
            error_message = (
                "This does not seem to be a preprint: the type "
                "returned by OSFPreprints on behalf of "
                "%(preprint_server) is %(type)s. "
                "Please contact techsupport."
            )
            raise forms.ValidationError(
                error_message,
                code="wrong_type",
                params={
                    "preprint_server": preprint_server.name,
                    "type": metadata["type"],
                },
            )
    else:
        raise forms.ValidationError(
            "OSFPreprints failed to return a type. Please contact techsupport.",
            code="wrong_type",
        )

    # TODO: Check if this article has already been published (according to OSFPreprints)

    identifier = preprint_server.name.lower() + "_" + osfpreprints_identifier
    return osfpreprints_data, metadata, identifier


def check_socarxiv_identifier(socarxiv_identifier):
    """
    Call `check_osfpreprints_identifier_w_vn_nr` but correct identifier
    by substituting `socarxiv` for `osfpreprints`.
    """
    data, metadata, identifier = check_osfpreprints_identifier(
        PreprintServer.objects.get(name="SocArXiv"), socarxiv_identifier
    )
    return data, metadata, identifier.replace("osfpreprints", "socarxiv")


class SubmissionPrefillForm(forms.Form):
    """
    Base class for all SubmissionPrefillForms (one per integrated preprint server).

    Based on kwargs `requested_by`, `journal_doi_label` and `thread_hash`,
    this prepares initial data for SubmissionForm.
    """

    def __init__(self, *args, **kwargs):
        self.requested_by = kwargs.pop("requested_by")
        self.journal = Journal.objects.get(doi_label=kwargs.pop("journal_doi_label"))
        self.thread_hash = kwargs.pop("thread_hash")

        if self.thread_hash:
            # Resubmission
            self.latest_submission = (
                Submission.objects.filter(thread_hash=self.thread_hash)
                .order_by("-submission_date", "-preprint")
                .first()
            )
        else:
            self.latest_submission = None
        super().__init__(*args, **kwargs)

    def is_resubmission(self):
        return self.latest_submission is not None

    def run_checks(self):
        """
        Consistency checks on the prefill data.
        """
        check_resubmission_readiness(self.requested_by, self.latest_submission)

    def get_prefill_data(self):
        form_data = {
            "acad_field": self.journal.college.acad_field,
            "submitted_to": self.journal,
        }
        if self.thread_hash:
            form_data["thread_hash"] = self.thread_hash
            form_data["is_resubmission_of"] = self.latest_submission.id
        return form_data


class SciPostPrefillForm(SubmissionPrefillForm):
    """
    Provide initial data for SubmissionForm (SciPost preprint server route).
    """

    def is_valid(self):
        """
        Accept an empty form as valid. Override Django BaseForm.is_valid

        Django BaseForm method requires is_bound == True and not self.errors.
        is_bound requires data is not None.
        We thus override is_valid by cutting the is_bound == True out.
        """
        return not self.errors

    def get_prefill_data(self):
        """
        Return initial form data originating from earlier Submission.
        """
        form_data = super().get_prefill_data()
        form_data["preprint_server"] = PreprintServer.objects.get(name="SciPost")
        if self.is_resubmission():
            form_data.update(
                {
                    "title": self.latest_submission.title,
                    "abstract": self.latest_submission.abstract,
                    "author_list": self.latest_submission.author_list,
                    "acad_field": self.latest_submission.acad_field,
                    "specialties": [
                        s.id for s in self.latest_submission.specialties.all()
                    ],
                    "approaches": self.latest_submission.approaches,
                    "referees_flagged": self.latest_submission.referees_flagged,
                    "referees_suggested": self.latest_submission.referees_suggested,
                }
            )
        return form_data


class ArXivPrefillForm(SubmissionPrefillForm):
    """
    Provide initial data for SubmissionForm (arXiv preprint server route).

    This adds the `arxiv_identifier_w_vn_nr` field to those
    from `SubmissionPrefillForm` base class.
    """

    arxiv_identifier_w_vn_nr = forms.RegexField(
        label="",
        regex=ARXIV_IDENTIFIER_PATTERN_NEW,
        strip=True,
        error_messages={"invalid": strings.arxiv_query_invalid},
        widget=forms.TextInput(),
    )

    def __init__(self, *args, **kwargs):
        self.arxiv_data = {}
        self.metadata = {}
        super().__init__(*args, **kwargs)

    def clean_arxiv_identifier_w_vn_nr(self):
        """
        Do basic prechecks based on the arXiv ID only.
        """
        identifier = self.cleaned_data.get("arxiv_identifier_w_vn_nr", None)

        check_identifier_is_unused(identifier)
        self.arxiv_data, self.metadata, identifier = check_arxiv_identifier_w_vn_nr(
            identifier
        )
        return identifier

    def get_prefill_data(self):
        """
        Return dictionary to prefill `SubmissionForm`.
        """
        form_data = super().get_prefill_data()
        form_data.update(self.arxiv_data)
        form_data["identifier_w_vn_nr"] = self.cleaned_data["arxiv_identifier_w_vn_nr"]
        if self.is_resubmission():
            form_data.update(
                {
                    "approaches": self.latest_submission.approaches,
                    "referees_flagged": self.latest_submission.referees_flagged,
                    "referees_suggested": self.latest_submission.referees_suggested,
                    "acad_field": self.latest_submission.acad_field,
                    "specialties": [
                        s.id for s in self.latest_submission.specialties.all()
                    ],
                }
            )
        return form_data


class ChemRxivPrefillForm(SubmissionPrefillForm):
    """
    Provide initial data for SubmissionForm from ChemRxiv
    (metadata actually collected from Crossref API, not ChemRxiv).

    This form is used by the ChemRxiv route (post-2021-07 style).
    """

    chemrxiv_doi = forms.RegexField(
        label="",
        regex=CHEMRXIV_DOI_PATTERN,
        strip=True,
        error_messages={"invalid": "Invalid ChemRxiv DOI"},
        widget=forms.TextInput(),
    )

    def __init__(self, *args, **kwargs):
        self.crossref_data = {}
        self.metadata = {}
        super().__init__(*args, **kwargs)

    def clean_chemrxiv_doi(self):
        # To get the identifier, strip the DOI prefix
        identifier = self.cleaned_data.get("chemrxiv_doi", None).partition("/")[2]

        check_identifier_is_unused(identifier)
        self.crossref_data, self.metadata, identifier = check_chemrxiv_doi(
            self.cleaned_data["chemrxiv_doi"]
        )
        return identifier

    def get_prefill_data(self):
        """
        Return dictionary to prefill `SubmissionForm`.
        """
        form_data = super().get_prefill_data()
        form_data.update(self.crossref_data)

        if self.is_resubmission():
            form_data.update(
                {
                    "approaches": self.latest_submission.approaches,
                    "referees_flagged": self.latest_submission.referees_flagged,
                    "referees_suggested": self.latest_submission.referees_suggested,
                    "acad_field": self.latest_submission.acad_field,
                    "specialties": [
                        s.id for s in self.latest_submission.specialties.all()
                    ],
                }
            )
        return form_data


class FigsharePrefillForm(SubmissionPrefillForm):
    """
    Provide initial data for SubmissionForm from Figshare.

    This form is used by the ChemRxiv (pre-2021-07), TechRxiv and Advance routes.
    """

    figshare_preprint_server = forms.ModelChoiceField(
        queryset=PreprintServer.objects.filter(served_by__name="Figshare"),
        widget=forms.HiddenInput(),
    )
    figshare_identifier_w_vn_nr = forms.RegexField(
        label="",
        regex=FIGSHARE_IDENTIFIER_PATTERN,
        strip=True,
        error_messages={"invalid": "Invalid Figshare identifier"},
        widget=forms.TextInput(),
    )

    def __init__(self, *args, **kwargs):
        self.figshare_data = {}
        self.metadata = {}
        self.identifier = None
        super().__init__(*args, **kwargs)

    def clean_figshare_identifier_w_vn_nr(self):
        """
        Do basic prechecks based on the Figshare identifier.
        """
        (
            self.figshare_data,
            self.metadata,
            self.identifier,
        ) = check_figshare_identifier_w_vn_nr(
            self.cleaned_data["figshare_preprint_server"],
            self.cleaned_data["figshare_identifier_w_vn_nr"],
        )
        check_identifier_is_unused(self.identifier)
        return self.cleaned_data["figshare_identifier_w_vn_nr"]

    def get_prefill_data(self):
        """
        Return dictionary to prefill `SubmissionForm`.
        """
        form_data = super().get_prefill_data()
        form_data.update(self.figshare_data)

        if self.is_resubmission():
            form_data.update(
                {
                    "approaches": self.latest_submission.approaches,
                    "referees_flagged": self.latest_submission.referees_flagged,
                    "referees_suggested": self.latest_submission.referees_suggested,
                    "acad_field": self.latest_submission.acad_field,
                    "specialties": [
                        s.id for s in self.latest_submission.specialties.all()
                    ],
                }
            )
        return form_data


class OSFPreprintsPrefillForm(SubmissionPrefillForm):
    """
    Provide initial data for SubmissionForm from OSFPreprints.

    This form is used by the SocArXiv (and others) routes.
    """

    osfpreprints_preprint_server = forms.ModelChoiceField(
        queryset=PreprintServer.objects.filter(served_by__name="OSFPreprints"),
        widget=forms.HiddenInput(),
    )
    osfpreprints_identifier = forms.RegexField(
        label="",
        regex=OSFPREPRINTS_IDENTIFIER_PATTERN,
        strip=True,
        error_messages={"invalid": "Invalid OSFPreprints identifier"},
        widget=forms.TextInput(),
    )

    def __init__(self, *args, **kwargs):
        self.osfpreprints_data = {}
        self.metadata = {}
        self.identifier = None
        super().__init__(*args, **kwargs)

    def clean_osfpreprints_identifier(self):
        """
        Do basic prechecks based on the OSFPreprints identifier.
        """
        (
            self.osfpreprints_data,
            self.metadata,
            self.identifier,
        ) = check_osfpreprints_identifier(
            self.cleaned_data["osfpreprints_preprint_server"],
            self.cleaned_data["osfpreprints_identifier"],
        )
        check_identifier_is_unused(self.identifier)
        return self.cleaned_data["osfpreprints_identifier"]

    def get_prefill_data(self):
        """
        Return dictionary to prefill `SubmissionForm`.
        """
        form_data = super().get_prefill_data()
        form_data.update(self.osfpreprints_data)

        if self.is_resubmission():
            form_data.update(
                {
                    "approaches": self.latest_submission.approaches,
                    "referees_flagged": self.latest_submission.referees_flagged,
                    "referees_suggested": self.latest_submission.referees_suggested,
                    "acad_field": self.latest_submission.acad_field,
                    "specialties": [
                        s.id for s in self.latest_submission.specialties.all()
                    ],
                }
            )
        return form_data


###################
#
# Submission form
#
###################


class SubmissionForm(forms.ModelForm):
    """
    Form to submit a new (re)Submission.
    """

    specialties = forms.ModelMultipleChoiceField(
        queryset=Specialty.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url="/ontology/specialty-autocomplete", attrs={"data-html": True}
        ),
        label="Specialties",
        help_text="Type to search, click to include",
    )
    preprint_server = forms.ModelChoiceField(
        queryset=PreprintServer.objects.all(), widget=forms.HiddenInput()
    )
    preprint_link = forms.URLField(widget=forms.HiddenInput())
    identifier_w_vn_nr = forms.CharField(widget=forms.HiddenInput())
    preprint_file = forms.FileField(
        help_text=(
            "Please submit the processed .pdf (not the source files; "
            "these will only be required at the post-acceptance proofs stage)"
        )
    )

    class Meta:
        model = Submission
        fields = [
            "is_resubmission_of",
            "thread_hash",
            "submitted_to",
            "proceedings",
            "acad_field",
            "specialties",
            "approaches",
            "title",
            "author_list",
            "abstract",
            "code_repository_url",
            "data_repository_url",
            "author_comments",
            "list_of_changes",
            "remarks_for_editors",
            "referees_suggested",
            "referees_flagged",
        ]
        widgets = {
            "submitted_to": forms.HiddenInput(),
            "acad_field": forms.HiddenInput(),
            "is_resubmission_of": forms.HiddenInput(),
            "thread_hash": forms.HiddenInput(),
            "code_repository_url": forms.TextInput(
                attrs={"placeholder": "If applicable; please give the full URL"}
            ),
            "data_repository_url": forms.TextInput(
                attrs={"placeholder": "If applicable; please give the full URL"}
            ),
            "remarks_for_editors": forms.Textarea(
                attrs={
                    "placeholder": "Any private remarks (for the editors only)",
                    "rows": 5,
                }
            ),
            "referees_suggested": forms.Textarea(
                attrs={
                    "placeholder": "Optional: names of suggested referees",
                    "rows": 5,
                }
            ),
            "referees_flagged": forms.Textarea(
                attrs={
                    "placeholder": (
                        "Optional: names of referees whose reports "
                        "should be treated with caution (+ short reason)"
                    ),
                    "rows": 5,
                }
            ),
            "author_comments": forms.Textarea(
                attrs={
                    "placeholder": "Your resubmission letter (will be viewable online)"
                }
            ),
            "list_of_changes": forms.Textarea(
                attrs={
                    "placeholder": (
                        "Give a point-by-point list of changes "
                        "(will be viewable online)"
                    )
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.requested_by = kwargs.pop("requested_by")
        self.submitted_to_journal = kwargs.pop("submitted_to_journal")
        data = args[0] if len(args) > 1 else kwargs.get("data", {})
        self.preprint_server = kwargs["initial"].get(
            "preprint_server", None
        ) or PreprintServer.objects.get(id=data.get("preprint_server"))
        self.thread_hash = kwargs["initial"].get("thread_hash", None) or data.get(
            "thread_hash"
        )
        self.is_resubmission_of = kwargs["initial"].get(
            "is_resubmission_of", None
        ) or data.get("is_resubmission_of")
        self.preprint_data = {}
        self.metadata = {}  # container for possible external server-provided metadata

        super().__init__(*args, **kwargs)

        if self.preprint_server.name == "SciPost":
            # SciPost identifier will be auto-generated
            del self.fields["identifier_w_vn_nr"]
            # Preprint will be linked directly from preprint file object
            del self.fields["preprint_link"]
        else:
            # No need for a file upload if user is not using the SciPost preprint server.
            del self.fields["preprint_file"]

        if not self.is_resubmission():
            del self.fields["is_resubmission_of"]
            del self.fields["author_comments"]
            del self.fields["list_of_changes"]

        # Restrict choice of specialties to those of relevant AcademicField
        if kwargs["initial"].get("acad_field", None):
            self.fields["specialties"].widget.url = (
                self.fields["specialties"].widget.url
                + "?acad_field_id="
                + str(kwargs["initial"].get("acad_field").id)
            )

        # Proceedings submission fields
        if "Proc" not in self.submitted_to_journal.doi_label:
            del self.fields["proceedings"]
        else:
            qs = self.fields["proceedings"].queryset.open_for_submission()
            self.fields["proceedings"].queryset = qs
            self.fields["proceedings"].empty_label = None
            if not qs.exists():
                del self.fields["proceedings"]

    def is_resubmission(self):
        return self.is_resubmission_of is not None

    def clean(self, *args, **kwargs):
        """
        Do all general checks for Submission.
        """
        cleaned_data = super().clean(*args, **kwargs)

        # SciPost preprints are auto-generated here.
        if "identifier_w_vn_nr" not in cleaned_data:
            cleaned_data["identifier_w_vn_nr"] = get_new_scipost_identifier(
                thread_hash=self.thread_hash
            )

        if self.is_resubmission():
            check_resubmission_readiness(
                self.requested_by, cleaned_data["is_resubmission_of"]
            )

        if "Codeb" in cleaned_data["submitted_to"].doi_label:
            if not ("code_repository_url" in cleaned_data and cleaned_data["code_repository_url"]):
                msg = (
                    "You must specify a code repository if you submit to %s"
                    % cleaned_data["submitted_to"].name
                )
                self.add_error("code_repository_url", msg)

        if "Proc" not in cleaned_data["submitted_to"].doi_label:
            try:
                del self.cleaned_data["proceedings"]
            except KeyError:
                # No proceedings returned to data
                pass
        return cleaned_data

    def clean_author_list(self):
        """
        Check if author list matches the Contributor submitting.
        """
        author_list = self.cleaned_data["author_list"]

        # Remove punctuation and convert to ASCII-only string.
        clean_author_name = to_ascii_only(self.requested_by.last_name)
        clean_author_list = to_ascii_only(author_list)

        if not clean_author_name in clean_author_list:
            error_message = (
                "Your name does not match that of any of the authors. "
                "You are not authorized to submit this preprint."
            )
            self.add_error("author_list", error_message)
        return author_list

    def clean_code_repository_url(self):
        """
        Prevent having well-known servers in list.
        """
        code_repository_url = self.cleaned_data["code_repository_url"]

        if "arxiv.org" in str(code_repository_url).lower():
            error_message = (
                "ArXiv.org is not a code repository; "
                "did you perhaps use the wrong form field?"
            )
            self.add_error("code_repository_url", error_message)
        return code_repository_url

    def clean_data_repository_url(self):
        """
        Prevent having well-known servers in list.
        """
        data_repository_url = self.cleaned_data["data_repository_url"]

        if "arxiv.org" in str(data_repository_url).lower():
            error_message = (
                "ArXiv.org is not a data repository; "
                "did you perhaps use the wrong form field?"
            )
            self.add_error("data_repository_url", error_message)
        return data_repository_url

    def clean_identifier_w_vn_nr(self):
        identifier = self.cleaned_data.get("identifier_w_vn_nr", None)

        check_identifier_is_unused(identifier)

        if self.preprint_server.name == "arXiv":
            (
                self.preprint_data,
                self.metadata,
                identifier,
            ) = check_arxiv_identifier_w_vn_nr(identifier)
        elif self.preprint_server.name == "ChemRxiv":
            self.preprint_data, self.metadata, identifier = check_chemrxiv_doi(
                identifier
            )
        elif self.preprint_server.name == "TechRxiv":
            (
                self.preprint_data,
                self.metadata,
                identifier,
            ) = check_techrxiv_identifier_w_vn_nr(identifier.replace("techrxiv_", ""))
        elif self.preprint_server.name == "Advance":
            (
                self.preprint_data,
                self.metadata,
                identifier,
            ) = check_advance_identifier_w_vn_nr(identifier.replace("advance_", ""))
        elif self.preprint_server.name == "SocArXiv":
            self.preprint_data, self.metadata, identifier = check_socarxiv_identifier(
                identifier.replace("socarxiv_", "")
            )
        else:
            error_message = (
                "Check method not implemented for preprint server: %s. "
                "Please contact techsupport."
            ) % self.preprint_server
            self.add_error("identifier_w_vn_nr", error_message)
        return identifier

    @transaction.atomic
    def save(self):
        """
        Create the new Submission and Preprint instances.
        """
        submission = super().save(commit=False)
        submission.submitted_by = self.requested_by.contributor

        # Save identifiers
        url = ""
        if self.cleaned_data.get("preprint_link", None):
            url = self.cleaned_data["preprint_link"]
        preprint, __ = Preprint.objects.get_or_create(
            identifier_w_vn_nr=self.cleaned_data["identifier_w_vn_nr"],
            url=url,
            _file=self.cleaned_data.get("preprint_file", None),
        )

        # Save metadata directly from preprint server call without possible user interception
        submission.metadata = self.metadata
        submission.preprint = preprint

        submission.save()

        # Explicitly handle specialties (otherwise they are not saved)
        submission.specialties.set(self.cleaned_data["specialties"])

        if self.is_resubmission():
            self.process_resubmission(submission)

        # Gather first known author and Fellows.
        submission.authors.add(self.requested_by.contributor)
        self.set_fellowship(submission)

        # Return latest version of the Submission. It could be outdated by now.
        submission.refresh_from_db()
        return submission

    def process_resubmission(self, submission):
        """
        Update all fields for new and old Submission and EditorialAssignments.

        -- submission: the new version of the Submission series.
        """
        if not submission.is_resubmission_of:
            raise Submission.DoesNotExist

        previous_submission = submission.is_resubmission_of

        # Close last submission
        Submission.objects.filter(id=previous_submission.id).update(
            is_current=False, open_for_reporting=False, status=STATUS_RESUBMITTED
        )

        # Copy Topics
        submission.topics.add(*previous_submission.topics.all())

        # Open for comments (reports: opened upon cycle choice) and copy EIC info
        Submission.objects.filter(id=submission.id).update(
            open_for_commenting=True,
            open_for_reporting=False,
            visible_public=previous_submission.visible_public,
            visible_pool=True,
            refereeing_cycle=CYCLE_UNDETERMINED,
            editor_in_charge=previous_submission.editor_in_charge,
            status=STATUS_EIC_ASSIGNED,
        )

        # Add author(s) (claim) fields
        submission.authors.add(*previous_submission.authors.all())
        submission.authors_claims.add(*previous_submission.authors_claims.all())
        submission.authors_false_claims.add(
            *previous_submission.authors_false_claims.all()
        )

        # Create new EditorialAssigment for the current Editor-in-Charge
        EditorialAssignment.objects.create(
            submission=submission,
            to=previous_submission.editor_in_charge,
            status=STATUS_ACCEPTED,
        )

    def set_fellowship(self, submission):
        """
        Set the default set of (guest) Fellows for this Submission.
        """
        qs = Fellowship.objects.active()
        fellows = (
            qs.regular_or_senior()
            .filter(
                college=submission.submitted_to.college,
                contributor__profile__specialties__in=submission.specialties.all(),
            )
            .return_active_for_submission(submission)
        )
        submission.fellows.set(fellows)

        if submission.proceedings:
            # Add (Regular or Guest) Fellowships if the Submission is a Proceedings manuscript
            guest_fellows = qs.filter(
                proceedings=submission.proceedings
            ).return_active_for_submission(submission)
            submission.fellows.add(*guest_fellows)


class SubmissionReportsForm(forms.ModelForm):
    """Update refereeing pdf for Submission."""

    class Meta:
        model = Submission
        fields = ["pdf_refereeing_pack"]


class PreassignEditorsForm(forms.ModelForm):
    """Preassign editors for incoming Submission."""

    assign = forms.BooleanField(required=False)
    to = forms.ModelChoiceField(
        queryset=Contributor.objects.none(), required=True, widget=forms.HiddenInput()
    )

    class Meta:
        model = EditorialAssignment
        fields = ("to",)

    def __init__(self, *args, **kwargs):
        self.submission = kwargs.pop("submission")
        super().__init__(*args, **kwargs)
        self.fields["to"].queryset = Contributor.objects.filter(
            fellowships__in=self.submission.fellows.all()
        )
        self.fields["assign"].initial = self.instance.id is not None

    def save(self, commit=True):
        """Create/get unordered EditorialAssignments or delete existing if needed."""
        if self.cleaned_data["assign"]:
            # Create/save
            self.instance, __ = EditorialAssignment.objects.get_or_create(
                submission=self.submission, to=self.cleaned_data["to"]
            )
        elif self.instance.id is not None:
            # Delete if exists
            if self.instance.status == STATUS_PREASSIGNED:
                self.instance.delete()
        return self.instance

    def get_fellow(self):
        """Get fellow either via initial data or instance."""
        if self.instance.id is not None:
            return self.instance.to
        return self.initial.get("to", None)


class BasePreassignEditorsFormSet(forms.BaseModelFormSet):
    """Preassign editors for incoming Submission."""

    def __init__(self, *args, **kwargs):
        self.submission = kwargs.pop("submission")
        super().__init__(*args, **kwargs)
        self.queryset = self.submission.editorial_assignments.order_by(
            "invitation_order"
        )

        # Prefill form fields and create unassigned rows for unassigned fellows.
        assigned_fellows = self.submission.fellows.filter(
            contributor__editorial_assignments__in=self.queryset
        )
        unassigned_fellows = self.submission.fellows.exclude(
            contributor__editorial_assignments__in=self.queryset
        )

        possible_assignments = [
            {ORDERING_FIELD_NAME: -1} for fellow in assigned_fellows
        ]
        for fellow in unassigned_fellows:
            possible_assignments.append(
                {
                    "submission": self.submission,
                    "to": fellow.contributor,
                    ORDERING_FIELD_NAME: -1,
                }
            )
        self.initial = possible_assignments
        self.extra += len(unassigned_fellows)

    def add_fields(self, form, index):
        """Force hidden input for ORDER field."""
        super().add_fields(form, index)
        if ORDERING_FIELD_NAME in form.fields:
            form.fields[ORDERING_FIELD_NAME].widget = forms.HiddenInput()

    def get_form_kwargs(self, index):
        """Add submission to form arguments."""
        kwargs = super().get_form_kwargs(index)
        kwargs["submission"] = self.submission
        return kwargs

    def save(self, commit=True):
        """Save each form and order EditorialAssignments."""
        objects = super().save(commit=False)
        objects = []

        count = 0
        for form in self.ordered_forms:
            ed_assignment = form.save()
            if ed_assignment.id is None:
                continue
            count += 1
            EditorialAssignment.objects.filter(id=ed_assignment.id).update(
                invitation_order=count
            )
            objects.append(ed_assignment)
        return objects


PreassignEditorsFormSet = forms.modelformset_factory(
    EditorialAssignment,
    can_order=True,
    extra=0,
    formset=BasePreassignEditorsFormSet,
    form=PreassignEditorsForm,
)


class SubmissionReassignmentForm(forms.ModelForm):
    """Process reassignment of EIC for Submission."""

    new_editor = forms.ModelChoiceField(
        queryset=Contributor.objects.none(), required=True
    )

    class Meta:
        model = Submission
        fields = ()

    def __init__(self, *args, **kwargs):
        """Add related submission as argument."""
        self.submission = kwargs.pop("submission")
        super().__init__(*args, **kwargs)

        self.fields["new_editor"].queryset = Contributor.objects.filter(
            fellowships__in=self.submission.fellows.all()
        ).exclude(id=self.submission.editor_in_charge.id)

    def save(self):
        """Update old/create new Assignment and send mails."""
        old_editor = self.submission.editor_in_charge
        old_assignment = (
            self.submission.editorial_assignments.ongoing()
            .filter(to=old_editor)
            .first()
        )
        if old_assignment:
            EditorialAssignment.objects.filter(id=old_assignment.id).update(
                status=STATUS_REPLACED
            )

        # Update Submission and update/create Editorial Assignments
        now = timezone.now()
        assignment = EditorialAssignment.objects.create(
            submission=self.submission,
            to=self.cleaned_data["new_editor"],
            status=STATUS_ACCEPTED,
            date_invited=now,
            date_answered=now,
        )
        self.submission.editor_in_charge = self.cleaned_data["new_editor"]
        self.submission.save()

        # Email old and new editor
        if old_assignment:
            mail_sender = DirectMailUtil(
                "fellows/email_fellow_replaced_by_other", assignment=old_assignment
            )
            mail_sender.send_mail()

        mail_sender = DirectMailUtil(
            "fellows/email_fellow_assigned_submission", assignment=assignment
        )
        mail_sender.send_mail()


class SubmissionTargetJournalForm(forms.ModelForm):
    """Change the target journal for the Submission."""

    class Meta:
        model = Submission
        fields = [
            "submitted_to",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["submitted_to"].queryset = Journal.objects.active()
        self.helper = FormHelper()
        self.helper.layout = Layout(
            FloatingField("submitted_to"),
            ButtonHolder(Submit("submit", "Update", css_class="btn btn-danger")),
        )


class SubmissionTargetProceedingsForm(forms.ModelForm):
    """Change the target Proceedings for the Submission."""

    class Meta:
        model = Submission
        fields = ["proceedings"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["proceedings"].queryset = Proceedings.objects.order_by(
            "-submissions_close"
        )
        self.fields["proceedings"].help_text = None
        self.helper = FormHelper()
        self.helper.layout = Layout(
            FloatingField("proceedings"),
            ButtonHolder(Submit("submit", "Update", css_class="btn btn-danger")),
        )


class SubmissionPreprintFileForm(forms.ModelForm):
    """Change the submitted pdf for the Submission."""

    class Meta:
        model = Preprint
        fields = ["_file"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            "_file",
            ButtonHolder(Submit("submit", "Update", css_class="btn btn-danger")),
        )


class SubmissionPrescreeningForm(forms.ModelForm):
    """Processing decision for pre-screening of Submission."""

    PASS, FAIL = "pass", "fail"
    CHOICES = (
        (PASS, "Pass pre-screening. Proceed to the Pool."),
        (FAIL, "Fail pre-screening."),
    )
    decision = forms.ChoiceField(
        widget=forms.RadioSelect, choices=CHOICES, required=False
    )

    message_for_authors = forms.CharField(
        required=False, widget=forms.Textarea({"placeholder": "Message for authors"})
    )
    remark_for_pool = forms.CharField(
        required=False, widget=forms.Textarea({"placeholder": "Remark for the pool"})
    )

    class Meta:
        model = Submission
        fields = ()

    def __init__(self, *args, **kwargs):
        """Add related submission as argument."""
        self.submission = kwargs.pop("submission")
        self.current_user = kwargs.pop("current_user")
        super().__init__(*args, **kwargs)

    def clean(self):
        """Check if Submission has right status."""
        data = super().clean()
        if self.instance.status != STATUS_INCOMING:
            self.add_error(None, "This Submission is currently not in pre-screening.")

        if data["decision"] == self.PASS:
            if not self.instance.fellows.exists():
                self.add_error(
                    None, "Please add at least one fellow to the pool first."
                )
            if not self.instance.editorial_assignments.exists():
                self.add_error(None, "Please complete the pre-assignments form first.")
        return data

    @transaction.atomic
    def save(self):
        """Update Submission status."""
        if self.cleaned_data["decision"] == self.PASS:
            Submission.objects.filter(id=self.instance.id).update(
                status=STATUS_UNASSIGNED, visible_pool=True, visible_public=False
            )
            self.instance.add_general_event("Submission passed pre-screening.")
        elif self.cleaned_data["decision"] == self.FAIL:
            EditorialAssignment.objects.filter(
                submission=self.instance
            ).invited().update(status=STATUS_DEPRECATED)
            Submission.objects.filter(id=self.instance.id).update(
                status=STATUS_FAILED_PRESCREENING,
                visible_pool=False,
                visible_public=False,
            )
            self.instance.add_general_event("Submission failed pre-screening.")
            mail_sender = DirectMailUtil(
                "prescreening_failed",
                instance=self.instance,
                message_for_authors=self.cleaned_data["message_for_authors"],
                header_template="submissions/admin/prescreening_failed.html",
            )
            mail_sender.send_mail()

        if self.cleaned_data["message_for_authors"]:
            Remark.objects.create(
                submission=self.instance,
                contributor=self.current_user.contributor,
                remark=self.cleaned_data["message_for_authors"],
            )
        if self.cleaned_data["remark_for_pool"]:
            Remark.objects.create(
                submission=self.instance,
                contributor=self.current_user.contributor,
                remark=self.cleaned_data["remark_for_pool"],
            )


class WithdrawSubmissionForm(forms.Form):
    """
    A submitting author has the right to withdraw the manuscript.
    """

    confirm = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=((True, "Confirm"), (False, "Abort")),
        label="",
    )

    def __init__(self, *args, **kwargs):
        """Add related submission as argument."""
        self.submission = kwargs.pop("submission")
        super().__init__(*args, **kwargs)

    def is_confirmed(self):
        return self.cleaned_data.get("confirm") in (True, "True")

    def save(self):
        if self.is_confirmed():
            # Update submission (current + any previous versions)
            Submission.objects.filter(id=self.submission.id).update(
                visible_public=False,
                visible_pool=False,
                open_for_commenting=False,
                open_for_reporting=False,
                status=STATUS_WITHDRAWN,
                latest_activity=timezone.now(),
            )
            self.submission.get_other_versions().update(visible_public=False)

            # Update all assignments
            EditorialAssignment.objects.filter(
                submission=self.submission
            ).need_response().update(status=STATUS_DEPRECATED)
            EditorialAssignment.objects.filter(
                submission=self.submission
            ).accepted().update(status=STATUS_COMPLETED)

            # Deprecate any outstanding recommendations
            if EICRecommendation.objects.filter(submission=self.submission).exists():
                EICRecommendation.objects.filter(
                    submission=self.submission
                ).active().update(status=DEPRECATED)

            # Update editorial decision
            if EditorialDecision.objects.filter(submission=self.submission).exists():
                decision = EditorialDecision.objects.filter(
                    submission=self.submission
                ).latest_version()
                decision.status = EditorialDecision.PUBOFFER_REFUSED_BY_AUTHORS
                decision.save()

            # Delete any production stream
            if hasattr(self.submission, "production_stream"):
                self.submission.production_stream.delete()

            self.submission.refresh_from_db()

        return self.submission


######################
# Editorial workflow #
######################


class EditorialAssignmentForm(forms.ModelForm):
    """Create and/or process new EditorialAssignment for Submission."""

    DECISION_CHOICES = (("accept", "Accept"), ("decline", "Decline"))
    CYCLE_CHOICES = (
        (CYCLE_DEFAULT, "Normal refereeing cycle"),
        (CYCLE_DIRECT_REC, "Directly formulate Editorial Recommendation for rejection"),
    )

    decision = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=DECISION_CHOICES,
        label="Are you willing to take charge of this Submission?",
    )
    refereeing_cycle = forms.ChoiceField(
        widget=forms.RadioSelect, choices=CYCLE_CHOICES, initial=CYCLE_DEFAULT
    )
    refusal_reason = forms.ChoiceField(choices=ASSIGNMENT_REFUSAL_REASONS)

    class Meta:
        model = EditorialAssignment
        fields = ()  # Don't use the default fields options because of the ordering of fields.

    def __init__(self, *args, **kwargs):
        """Add related submission as argument."""
        self.submission = kwargs.pop("submission")
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)
        if not self.instance.id:
            del self.fields["decision"]
            del self.fields["refusal_reason"]

    def has_accepted_invite(self):
        """Check if invite is accepted or if voluntered to become EIC."""
        return (
            "decision" not in self.cleaned_data
            or self.cleaned_data["decision"] == "accept"
        )

    def is_normal_cycle(self):
        """Check if normal refereeing cycle is chosen."""
        return self.cleaned_data["refereeing_cycle"] == CYCLE_DEFAULT

    def save(self, commit=True):
        """Save Submission to EditorialAssignment."""
        self.instance.submission = self.submission
        self.instance.date_answered = timezone.now()
        self.instance.to = self.request.user.contributor
        assignment = super().save()  # Save already, in case it's a new recommendation.

        if self.has_accepted_invite():
            # Update related Submission.
            if self.is_normal_cycle():
                # Default Refereeing process
                deadline = (
                    timezone.now()
                    + self.instance.submission.submitted_to.refereeing_period
                )

                # Update related Submission.
                Submission.objects.filter(id=self.submission.id).update(
                    refereeing_cycle=CYCLE_DEFAULT,
                    status=STATUS_EIC_ASSIGNED,
                    editor_in_charge=self.request.user.contributor,
                    reporting_deadline=deadline,
                    open_for_reporting=True,
                    open_for_commenting=True,
                    visible_public=True,
                    latest_activity=timezone.now(),
                )
                # Refresh the instance
                self.instance.submission = Submission.objects.get(id=self.submission.id)
            else:
                # Direct editorial recommendation
                visible_public = False
                if self.instance.submission.is_resubmission_of:
                    visible_public = (
                        self.instance.submission.is_resubmission_of.visible_public
                    )
                Submission.objects.filter(id=self.submission.id).update(
                    refereeing_cycle=CYCLE_DIRECT_REC,
                    status=STATUS_EIC_ASSIGNED,
                    editor_in_charge=self.request.user.contributor,
                    reporting_deadline=timezone.now(),
                    open_for_reporting=False,
                    open_for_commenting=True,
                    visible_public=visible_public,
                    latest_activity=timezone.now(),
                )
                # Refresh the instance
                self.instance.submission = Submission.objects.get(id=self.submission.id)

            # Implicitly or explicity accept the assignment and deprecate others.
            # assignment.accepted = True  # Deprecated field
            assignment.status = STATUS_ACCEPTED

            # Update all other 'open' invitations
            EditorialAssignment.objects.filter(
                submission=self.submission
            ).need_response().exclude(id=assignment.id).update(status=STATUS_DEPRECATED)
        else:
            # assignment.accepted = False  # Deprecated field
            assignment.status = STATUS_DECLINED
            assignment.refusal_reason = self.cleaned_data["refusal_reason"]
        assignment.save()  # Save again to register acceptance
        return assignment


class ConsiderAssignmentForm(forms.Form):
    """Process open EditorialAssignment."""

    accept = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=ASSIGNMENT_BOOL,
        label="Are you willing to take charge of this Submission?",
    )
    refusal_reason = forms.ChoiceField(
        choices=ASSIGNMENT_REFUSAL_REASONS, required=False
    )


class RefereeSearchForm(forms.Form):
    last_name = forms.CharField(
        widget=forms.TextInput(
            {"placeholder": "Search for a referee in the SciPost Profiles database"}
        )
    )

    def search(self):
        query = Q_with_alternative_spellings(
            last_name__icontains=self.cleaned_data["last_name"]
        )
        return (
            Profile.objects.filter(query)
            .exclude(contributor__user__is_superuser=True)
            .exclude(contributor__user__is_staff=True)
        )


class ConsiderRefereeInvitationForm(forms.Form):
    accept = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=ASSIGNMENT_BOOL,
        label="Are you willing to referee this Submission?",
    )
    refusal_reason = forms.ChoiceField(
        choices=ASSIGNMENT_REFUSAL_REASONS, required=False
    )


class SetRefereeingDeadlineForm(forms.Form):
    deadline = forms.DateField(
        label="",
        widget=forms.SelectDateWidget(
            years=[timezone.now().year + i for i in range(2)],
            empty_label=("Year", "Month", "Day"),
        ),
    )

    def clean_deadline(self):
        if not (self.cleaned_data.get("deadline") >= timezone.now().date()):
            self.add_error("deadline", "Please choose a future date!")
        return self.cleaned_data.get("deadline")


class VotingEligibilityForm(forms.ModelForm):
    """Assign Fellows to vote for EICRecommendation and open its status for voting."""

    eligible_fellows = forms.ModelMultipleChoiceField(
        queryset=Contributor.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        required=True,
        label="Eligible for voting",
    )

    class Meta:
        model = EICRecommendation
        fields = ()

    def __init__(self, *args, **kwargs):
        """Get queryset of Contributors eligible for voting."""
        super().__init__(*args, **kwargs)

        # If there exists a previous recommendation, include previous voting Fellows:
        prev_elig_id = []
        for prev_rec in self.instance.submission.eicrecommendations.all():
            prev_elig_id += [fellow.id for fellow in prev_rec.eligible_to_vote.all()]
        eligible = (
            Contributor.objects.filter(fellowships__pool=self.instance.submission)
            .filter(
                Q(EIC=self.instance.submission)
                | Q(profile__specialties__in=self.instance.submission.specialties.all())
                | Q(pk__in=prev_elig_id)
            )
            .order_by("user__last_name")
            .distinct()
        )

        self.fields["eligible_fellows"].queryset = eligible

    def save(self, commit=True):
        """Update EICRecommendation status and save its voters."""
        self.instance.eligible_to_vote.set(self.cleaned_data["eligible_fellows"])
        self.instance.status = PUT_TO_VOTING

        if commit:
            self.instance.save()
            self.instance.submission.touch()
            self.instance.voted_for.add(self.instance.submission.editor_in_charge)
        return self.instance

    def get_eligible_fellows(self):
        return self.fields["eligible_fellows"].queryset


############
# Reports:
############


class ReportPDFForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["pdf_report"]


class ReportForm(forms.ModelForm):
    """Write Report form."""

    report_type = REPORT_NORMAL

    class Meta:
        model = Report
        fields = [
            "qualification",
            "strengths",
            "weaknesses",
            "report",
            "requested_changes",
            "validity",
            "significance",
            "originality",
            "clarity",
            "formatting",
            "grammar",
            "recommendation",
            "remarks_for_editors",
            "file_attachment",
            "anonymous",
        ]

    def __init__(self, *args, **kwargs):
        if kwargs.get("instance"):
            if kwargs["instance"].is_followup_report:
                # Prefill data from latest report in the series
                latest_report = kwargs["instance"].latest_report_from_thread()
                kwargs.update(
                    {
                        "initial": {
                            "qualification": latest_report.qualification,
                            "anonymous": latest_report.anonymous,
                        }
                    }
                )

        self.submission = kwargs.pop("submission")

        super().__init__(*args, **kwargs)
        self.fields["strengths"].widget.attrs.update(
            {
                "placeholder": (
                    "Give a point-by-point "
                    "(numbered 1-, 2-, ...) list of the paper's strengths"
                ),
                "rows": 10,
                "cols": 100,
            }
        )
        self.fields["weaknesses"].widget.attrs.update(
            {
                "placeholder": (
                    "Give a point-by-point "
                    "(numbered 1-, 2-, ...) list of the paper's weaknesses"
                ),
                "rows": 10,
                "cols": 100,
            }
        )
        self.fields["report"].widget.attrs.update(
            {
                "placeholder": "Your general remarks. Are this Journal's acceptance criteria met? Would you recommend publication in another Journal instead?",
                "rows": 10,
                "cols": 100,
            }
        )
        self.fields["requested_changes"].widget.attrs.update(
            {
                "placeholder": "Give a numbered (1-, 2-, ...) list of specifically requested changes",
                "cols": 100,
            }
        )

        self.fields[
            "file_attachment"
        ].label = "File attachment (2MB limit; for a figure or similar - please avoid annotated pdfs)"

        # Required fields on submission; optional on save as draft
        if "save_submit" in self.data:
            required_fields = ["report", "recommendation"]
        else:
            required_fields = []
        required_fields_label = ["report", "recommendation"]

        for field in required_fields:
            self.fields[field].required = True

        # Let user know the field is required!
        for field in required_fields_label:
            self.fields[field].label += " *"

        if self.submission.eicrecommendations.active().exists():
            # An active EICRecommendation is already formulated. This Report will be flagged.
            self.report_type = REPORT_POST_EDREC

    def save(self):
        """
        Update meta data if ModelForm is submitted (non-draft).
        Possibly overwrite the default status if user asks for saving as draft.
        """
        report = super().save(commit=False)
        report.report_type = self.report_type

        report.submission = self.submission
        report.date_submitted = timezone.now()

        # Save with right status asked by user
        if "save_draft" in self.data:
            report.status = STATUS_DRAFT
        elif "save_submit" in self.data:
            report.status = STATUS_UNVETTED

            # Update invitation and report meta data if exist
            updated_invitations = self.submission.referee_invitations.filter(
                referee=report.author
            ).update(fulfilled=True)
            if updated_invitations > 0:
                report.invited = True

            # Check if report author if the report is being flagged on the submission
            if self.submission.referees_flagged:
                if report.author.user.last_name in self.submission.referees_flagged:
                    report.flagged = True
        report.save()
        return report


class VetReportForm(forms.Form):
    action_option = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=REPORT_ACTION_CHOICES,
        required=True,
        label="Action",
    )
    refusal_reason = forms.ChoiceField(choices=REPORT_REFUSAL_CHOICES, required=False)
    email_response_field = forms.CharField(
        widget=forms.Textarea(), label="Justification (optional)", required=False
    )

    def __init__(self, *args, **kwargs):
        self.report = kwargs.pop("report", None)
        super().__init__(*args, **kwargs)
        self.fields["email_response_field"].widget.attrs.update(
            {
                "placeholder": (
                    "Optional: give a textual justification "
                    "(will be included in the email to the Report's author)"
                ),
                "rows": 5,
            }
        )

    def clean_refusal_reason(self):
        """Require a refusal reason if report is rejected."""
        reason = self.cleaned_data["refusal_reason"]
        if self.cleaned_data["action_option"] == REPORT_ACTION_REFUSE:
            if not reason:
                self.add_error(
                    "refusal_reason", "A reason must be given to refuse a report."
                )
        return reason

    def process_vetting(self, current_contributor):
        """Set the right report status and update submission fields if needed."""
        report = self.report
        if self.cleaned_data["action_option"] == REPORT_ACTION_ACCEPT:
            # Accept the report as is
            Report.objects.filter(id=report.id).update(
                status=STATUS_VETTED,
                vetted_by=current_contributor,
            )
            report.submission.touch()
        elif self.cleaned_data["action_option"] == REPORT_ACTION_REFUSE:
            # The report is rejected
            Report.objects.filter(id=report.id).update(
                status=self.cleaned_data["refusal_reason"],
            )
        else:
            raise exceptions.InvalidReportVettingValue(
                self.cleaned_data["action_option"]
            )
        report.refresh_from_db()
        return report


###################
# Communications #
###################


class EditorialCommunicationForm(forms.ModelForm):
    class Meta:
        model = EditorialCommunication
        fields = ("text",)
        widgets = {
            "text": forms.Textarea(
                attrs={"rows": 5, "placeholder": "Write your message in this box."}
            ),
        }


######################
# EIC Recommendation #
######################


class EICRecommendationForm(forms.ModelForm):
    """Formulate an EICRecommendation."""

    DAYS_TO_VOTE = 7
    assignment = None
    earlier_recommendations = []

    tier = forms.ChoiceField(
        widget=forms.RadioSelect, choices=SUBMISSION_TIERS, required=False
    )

    class Meta:
        model = EICRecommendation
        fields = [
            "for_journal",
            "recommendation",
            "tier",
            "remarks_for_authors",
            "requested_changes",
            "remarks_for_editorial_college",
        ]
        widgets = {
            "remarks_for_authors": forms.Textarea(
                {
                    "placeholder": (
                        "Your remarks for the authors. If you recommend to accept or reject, will"
                        " only be seen after the college vote concludes."
                    ),
                    "rows": 10,
                }
            ),
            "requested_changes": forms.Textarea(
                {
                    "placeholder": (
                        "If you request revisions, give a numbered (1-, 2-, ...)"
                        " list of specifically requested changes"
                    ),
                }
            ),
            "remarks_for_editorial_college": forms.Textarea(
                {
                    "placeholder": (
                        "If you recommend to accept or reject the manuscript, the Editorial College"
                        " will vote. Summarize the reasons for your recommendation. Focus especially"
                        " on the aspects that do not directly follow from the referee reports."
                    ),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        """Accept two additional kwargs.

        -- submission: The Submission to formulate an EICRecommendation for.
        -- reformulate (bool): Reformulate the currently available EICRecommendations.
        """
        self.submission = kwargs.pop("submission")
        self.reformulate = kwargs.pop("reformulate", False)
        self.load_earlier_recommendations()

        if self.reformulate:
            latest_recommendation = self.earlier_recommendations.first()
            if latest_recommendation:
                kwargs["initial"] = {
                    "for_journal": latest_recommendation.for_journal,
                    "recommendation": latest_recommendation.recommendation,
                }

        super().__init__(*args, **kwargs)
        for_journal_qs = Journal.objects.active().filter(
            # The journals which can be recommended for are those falling under
            # the responsibility of the College of the journal submitted to
            college=self.submission.submitted_to.college
        )
        if self.submission.submitted_to.name.partition(" ")[0] == "SciPost":
            # Submitted to a SciPost journal, so Selections is accessible
            for_journal_qs = for_journal_qs | Journal.objects.filter(
                name="SciPost Selections"
            )
        self.fields["for_journal"].queryset = for_journal_qs
        if self.submission.submitted_to.name.partition(" ")[0] == "SciPost":
            # Submitted to a SciPost journal, so Core and Selections are accessible
            self.fields["for_journal"].help_text = (
                "Please be aware of all the points below!"
                "<ul><li>SciPost Selections: means article in field flagship journal "
                "(SciPost Physics, Astronomy, Biology, Chemistry...) "
                "with extended abstract published separately in SciPost Selections. "
                "Only choose this for "
                "an <em>exceptionally</em> good submission to a flagship journal.</li>"
                "<li>A submission to a flaghip which does not meet the latter's "
                "tough expectations and criteria can be recommended for publication "
                "in the field's Core journal (if it exists).</li>"
                "<li>Conversely, an extremely good submission to a field's Core journal can be "
                "recommended for publication in the field's flagship, provided "
                "it fulfils the latter's expectations and criteria.</li>"
                "</ul>"
            )
        self.fields["recommendation"].help_text = (
            "Selecting any of the three Publish choices means that you recommend publication.<br>"
            "Which one you choose simply indicates your ballpark evaluation of the "
            "submission's quality and has no further consequence on the publication."
        )
        self.load_assignment()

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data["recommendation"] == EIC_REC_PUBLISH:
            if not cleaned_data["for_journal"]:
                raise forms.ValidationError(
                    "If you recommend Publish, please specify for which Journal."
                )
            if cleaned_data["tier"] == "":
                raise forms.ValidationError(
                    "If you recommend Publish, please also provide a Tier."
                )
        if (
            cleaned_data["recommendation"] in (EIC_REC_PUBLISH, EIC_REC_REJECT)
            and len(cleaned_data["remarks_for_editorial_college"]) < 10
        ):
            raise forms.ValidationError(
                "You must substantiate your recommendation to accept or reject the manuscript."
            )

    def save(self):
        # If the cycle hadn't been chosen, set it to the DirectCycle
        if not self.submission.refereeing_cycle:
            self.submission.refereeing_cycle = CYCLE_DIRECT_REC
            self.submission.save()

        recommendation = super().save(commit=False)
        recommendation.submission = self.submission
        recommendation.voting_deadline += datetime.timedelta(
            days=self.DAYS_TO_VOTE
        )  # Test this
        recommendation.version = len(self.earlier_recommendations) + 1

        # Delete any previous tierings (irrespective of new/updated recommendation):
        SubmissionTiering.objects.filter(
            submission=self.submission, fellow=self.submission.editor_in_charge
        ).delete()

        if self.reformulate:
            event_text = (
                "The Editorial Recommendation has been reformulated for Journal {}: {}."
            )
        else:
            event_text = (
                "An Editorial Recommendation has been formulated for Journal {}: {}."
            )

        if recommendation.recommendation in [
            EIC_REC_MINOR_REVISION,
            EIC_REC_MAJOR_REVISION,
        ]:
            # Minor/Major revision: return to Author; ask to resubmit
            recommendation.status = DECISION_FIXED
            Submission.objects.filter(id=self.submission.id).update(
                open_for_reporting=False,
                open_for_commenting=False,
                reporting_deadline=timezone.now(),
            )

            if self.assignment:
                # The EIC has fulfilled this editorial assignment.
                self.assignment.status = STATUS_COMPLETED
                self.assignment.save()

            # Add SubmissionEvents for both Author and EIC
            self.submission.add_general_event(
                event_text.format(
                    str(recommendation.for_journal),
                    recommendation.get_recommendation_display(),
                )
            )
        else:
            # if rec is to publish, specify the tiering (deleting old ones first):
            if recommendation.recommendation == EIC_REC_PUBLISH:
                tiering = SubmissionTiering(
                    submission=self.submission,
                    fellow=self.submission.editor_in_charge,
                    for_journal=recommendation.for_journal,
                    tier=self.cleaned_data["tier"],
                )
                tiering.save()

            # Add SubmissionEvent for EIC only
            self.submission.add_event_for_eic(
                event_text.format(
                    str(recommendation.for_journal),
                    recommendation.get_recommendation_display(),
                )
            )

        if self.earlier_recommendations:
            self.earlier_recommendations.update(active=False, status=DEPRECATED)

            # All reports already submitted are now formulated *after* eic rec formulation
            Report.objects.filter(
                submission__eicrecommendations__in=self.earlier_recommendations
            ).update(report_type=REPORT_NORMAL)

        recommendation.save()

        return recommendation

    def revision_requested(self):
        return self.instance.recommendation in [
            EIC_REC_MINOR_REVISION,
            EIC_REC_MAJOR_REVISION,
        ]

    def has_assignment(self):
        return self.assignment is not None

    def load_assignment(self):
        # Find EditorialAssignment for Submission
        try:
            self.assignment = self.submission.editorial_assignments.accepted().get(
                to=self.submission.editor_in_charge
            )
            return True
        except EditorialAssignment.DoesNotExist:
            return False

    def load_earlier_recommendations(self):
        """Load and save EICRecommendations related to Submission of the instance."""
        self.earlier_recommendations = self.submission.eicrecommendations.all()


###############
# Vote form #
###############


class RecommendationVoteForm(forms.Form):
    """Cast vote on EICRecommendation form."""

    vote = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=[("agree", "Agree"), ("disagree", "Disagree"), ("abstain", "Abstain")],
    )
    tier = forms.ChoiceField(
        widget=forms.RadioSelect, choices=SUBMISSION_TIERS, required=False
    )
    alternative_for_journal = forms.ModelChoiceField(
        label="Alternative recommendation: for which Journal?",
        widget=forms.Select,
        queryset=Journal.objects.active(),
        required=False,
    )
    alternative_recommendation = forms.ChoiceField(
        label="Which action do you recommend?",
        widget=forms.Select,
        choices=ALT_REC_CHOICES,
        required=False,
    )
    remark = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "cols": 30,
                "placeholder": "Any further remark you want to add? (optional)",
            }
        ),
        label="",
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data["vote"] == "disagree" and (
            cleaned_data["alternative_for_journal"] is None
            or cleaned_data["alternative_recommendation"] == ""
        ):
            raise forms.ValidationError(
                "If you disagree, you must provide an alternative recommendation "
                "(by filling both the for journal and recommendation fields)."
            )


class EditorialDecisionForm(forms.ModelForm):
    """For EdAdmin to fix the outcome on a Submission, after voting is completed."""

    class Meta:
        model = EditorialDecision
        fields = [
            "submission",
            "for_journal",
            "decision",
            "taken_on",
            "remarks_for_authors",
            "remarks_for_editorial_college",
            "status",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["submission"].disabled = True
        self.fields["remarks_for_authors"].widget.attrs.update(
            {"placeholder": "[will be seen by authors and Fellows]"}
        )
        self.fields["remarks_for_editorial_college"].widget.attrs.update(
            {"placeholder": "[will only be seen by Fellows]"}
        )

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data["decision"] == EIC_REC_REJECT
            and cleaned_data["status"] == EditorialDecision.AWAITING_PUBOFFER_ACCEPTANCE
        ):
            raise forms.ValidationError(
                "If the decision is to reject, the status cannot be "
                "Awaiting author acceptance of publication offer."
            )

    def save(self):
        decision = super().save(commit=False)
        if not self.instance.id:  # a new object is created
            if self.cleaned_data["submission"].editorialdecision_set.all().exists():
                decision.version = (
                    self.cleaned_data["submission"]
                    .editorialdecision_set.all()
                    .latest_version()
                    .version
                    + 1
                )
        decision.save()
        return decision


class RestartRefereeingForm(forms.Form):
    """
    For EdAdmin to restart the latest refereeing round.
    """

    confirm = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=((True, "Confirm"), (False, "Abort")),
        label="",
    )

    def __init__(self, *args, **kwargs):
        """Add related submission as argument."""
        self.submission = kwargs.pop("submission")
        super().__init__(*args, **kwargs)

    def is_confirmed(self):
        return self.cleaned_data.get("confirm") in (True, "True")

    def save(self):
        if self.is_confirmed():
            Submission.objects.filter(id=self.submission.id).update(
                status=STATUS_EIC_ASSIGNED,
                refereeing_cycle=CYCLE_UNDETERMINED,
                acceptance_date=None,
                latest_activity=timezone.now(),
            )
            self.submission.editorial_assignments.filter(
                to=self.submission.editor_in_charge, status=STATUS_COMPLETED
            ).update(status=STATUS_ACCEPTED)
            self.submission.eicrecommendations.active().update(status=DEPRECATED)

            # Delete any production stream
            if hasattr(self.submission, "production_stream"):
                self.submission.production_stream.delete()

            self.submission.refresh_from_db()
        return self.submission


class SubmissionCycleChoiceForm(forms.ModelForm):
    """
    For the EIC to take a decision on the Submission's cycle. Used for resubmissions only.
    """

    referees_reinvite = forms.ModelMultipleChoiceField(
        queryset=RefereeInvitation.objects.none(),
        widget=forms.CheckboxSelectMultiple({"checked": "checked"}),
        required=False,
        label="Reinvite referees",
    )

    class Meta:
        model = Submission
        fields = ("refereeing_cycle",)
        widgets = {"refereeing_cycle": forms.RadioSelect}

    def __init__(self, *args, **kwargs):
        """Update choices and queryset."""
        super().__init__(*args, **kwargs)
        self.fields["refereeing_cycle"].choices = SUBMISSION_CYCLE_CHOICES
        other_submissions = self.instance.other_versions.all()
        if other_submissions:
            self.fields[
                "referees_reinvite"
            ].queryset = RefereeInvitation.objects.filter(
                submission__in=other_submissions
            ).distinct()

    def save(self):
        """
        If the cycle is for a normal or short refereeing round, open the sub for reporting.
        """
        if self.cleaned_data["refereeing_cycle"] in [CYCLE_DEFAULT, CYCLE_SHORT]:
            self.instance.open_for_reporting = True
        return super().save()


class iThenticateReportForm(forms.ModelForm):
    class Meta:
        model = iThenticateReport
        fields = []

    def __init__(self, submission, *args, **kwargs):
        self.submission = submission
        super().__init__(*args, **kwargs)

        if kwargs.get("files", {}).get("file"):
            # Add file field if file data is coming in!
            self.fields["file"] = forms.FileField()

    def clean(self):
        cleaned_data = super().clean()
        doc_id = self.instance.doc_id
        if not doc_id and not self.fields.get("file"):
            try:
                # cleaned_data['document'] = helpers.retrieve_pdf_from_arxiv(
                #     self.submission.preprint.identifier_w_vn_nr)
                cleaned_data["document"] = self.submission.preprint.get_document()
            except exceptions.PreprintDocumentNotFoundError:
                self.add_error(
                    None, "Preprint document not found. Please upload the pdf manually."
                )
                self.fields[
                    "file"
                ] = forms.FileField()  # Add this field now it's needed
        elif not doc_id and cleaned_data.get("file"):
            cleaned_data["document"] = cleaned_data["file"].read()
        elif doc_id:
            self.document_id = doc_id

        # Login client to append login-check to form
        self.client = self.get_client()

        if not self.client:
            return None

        # Document (id) is found
        if cleaned_data.get("document"):
            self.document = cleaned_data["document"]

        self.response = self.call_ithenticate()

        if hasattr(self, "response") and self.response:
            return cleaned_data

        # Don't return anything as someone submitted invalid data for the form at this point!
        return None

    def save(self, *args, **kwargs):
        data = self.response

        report, created = iThenticateReport.objects.get_or_create(doc_id=data["id"])

        if not created:
            try:
                iThenticateReport.objects.filter(doc_id=data["id"]).update(
                    uploaded_time=data["uploaded_time"],
                    processed_time=data["processed_time"],
                    percent_match=data["percent_match"],
                    part_id=data.get("parts", [{}])[0].get("id"),
                )
            except KeyError:
                pass
        else:
            report.save()
            Submission.objects.filter(id=self.submission.id).update(
                plagiarism_report=report
            )
        return report

    def call_ithenticate(self):
        if hasattr(self, "document_id"):
            # Update iThenticate status
            return self.update_status()
        elif hasattr(self, "document"):
            # Upload iThenticate document first time
            return self.upload_document()

    def get_client(self):
        client = iThenticate.API.Client(
            settings.ITHENTICATE_USERNAME, settings.ITHENTICATE_PASSWORD
        )
        if client.login():
            return client
        self.add_error(None, "Failed to login to iThenticate.")
        return None

    def update_status(self):
        client = self.client
        response = client.documents.get(self.document_id)
        if response["status"] == 200:
            return response.get("data")[0].get("documents")[0]
        self.add_error(
            None, "Updating failed. iThenticate didn't return valid data [1]"
        )

        for msg in client.messages:
            self.add_error(None, msg)
        return None

    def upload_document(self):
        from .plagiarism import iThenticate

        plagiarism = iThenticate()
        data = plagiarism.upload_submission(self.document, self.submission)

        # Give feedback to the user
        if not data:
            self.add_error(
                None, "Updating failed. iThenticate didn't return valid data [3]"
            )
            for msg in plagiarism.get_messages():
                self.add_error(None, msg)
            return None
        return data
