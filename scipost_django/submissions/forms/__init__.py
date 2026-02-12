__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from itertools import product
from django.urls import reverse, reverse_lazy
from django.utils.timezone import timedelta

from colleges.permissions import is_edadmin
from common.forms import CrispyFormMixin, HTMXDynSelWidget, SearchForm
from common.utils.text import partial_names_match
from ethics.managers import CoauthorshipExclusionPurpose
from submissions.models.assignment import ConditionalAssignmentOffer


import datetime

from django import forms
from django.conf import settings
from django.db import transaction
from django.db.models import (
    Q,
    Count,
    Exists,
    OuterRef,
    QuerySet,
    Value,
    BooleanField,
    ExpressionWrapper,
)
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404
from django.forms.formsets import ORDERING_FIELD_NAME
from django.utils import timezone

from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    Layout,
    Div,
    Field,
    ButtonHolder,
    Submit,
    Button,
    HTML,
    Fieldset,
)
from crispy_bootstrap5.bootstrap5 import FloatingField

from dal import autocomplete

from ..constants import (
    REPORT_ACTION_CHOICES,
    REPORT_REFUSAL_CHOICES,
    REPORT_POST_EDREC,
    REPORT_NORMAL,
    STATUS_DRAFT,
    STATUS_UNVETTED,
    REPORT_ACTION_ACCEPT,
    REPORT_ACTION_REFUSE,
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
)
from .. import exceptions
from ..helpers import to_ascii_only
from ..models import (
    PreprintServer,
    SubmissionAuthorProfile,
    Submission,
    RefereeInvitation,
    Report,
    EICRecommendation,
    EditorialAssignment,
    SubmissionTiering,
    EditorialDecision,
    PlagiarismAssessment,
    iThenticateReport,
    EditorialCommunication,
    RefereeIndication,
)

from colleges.models import Fellowship
from common.utils import remove_extra_spacing
from journals.models import Journal, Publication
from journals.constants import (
    PUBLISHABLE_OBJECT_TYPE_ARTICLE,
    PUBLISHABLE_OBJECT_TYPE_CODEBASE,
    PUBLISHABLE_OBJECT_TYPE_DATASET,
)
from mails.utils import DirectMailUtil
from ontology.models import Specialty, Topic
from preprints.helpers import get_new_scipost_identifier
from preprints.models import Preprint
from proceedings.models import Proceedings
from profiles.models import Profile, ProfileEmail
from scipost.services import (
    ChemRxivCaller,
    ArxivCaller,
    FigshareCaller,
    OSFPreprintsCaller,
)
from scipost.models import Contributor, Remark, UnavailabilityPeriod
from series.models import Collection
import strings

import iThenticate

ARXIV_IDENTIFIER_PATTERN_NEW = r"^[0-9]{4,}\.[0-9]{4,5}v[0-9]{1,2}$"
FIGSHARE_IDENTIFIER_PATTERN = r"^[0-9]+\.v[0-9]{1,2}$"
OSFPREPRINTS_IDENTIFIER_PATTERN = r"^[a-z0-9]+(_v\d{1,2})?$"


class PortalSubmissionSearchForm(CrispyFormMixin, SearchForm[Submission]):
    model = Submission
    queryset = Submission.objects.public_latest()

    author = forms.CharField(max_length=100, required=False, label="Author(s)")
    title = forms.CharField(max_length=512, required=False)
    submitted_to = forms.ModelChoiceField(
        queryset=Journal.objects.active(), required=False
    )
    identifier = forms.CharField(max_length=128, required=False)
    proceedings = forms.ModelChoiceField(
        queryset=Proceedings.objects.order_by("-submissions_close"), required=False
    )
    date_after = forms.DateField(
        required=False,
        label="Submitted after",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    date_before = forms.DateField(
        required=False,
        label="Submitted before",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    orderby = forms.ChoiceField(
        label="Order by",
        choices=(("submission_date", "Submission date"),),
        required=False,
        initial="submission_date",
    )

    def __init__(self, *args, **kwargs):
        self.acad_field_slug = kwargs.pop("acad_field_slug")
        self.specialty_slug = kwargs.pop("specialty_slug")
        super().__init__(*args, **kwargs)
        if (acad_field_slug := self.acad_field_slug) and self.acad_field_slug != "all":
            self.fields["submitted_to"].queryset = Journal.objects.filter(
                college__acad_field__slug=acad_field_slug
            )

    def get_form_layout(self) -> Layout:
        return Layout(
            Div(
                Div(FloatingField("title"), css_class="col-lg-9"),
                Div(FloatingField("identifier"), css_class="col-lg-3"),
                css_class="row mb-0",
            ),
            Div(
                Div(FloatingField("submitted_to"), css_class="col-lg-6"),
                Div(FloatingField("proceedings"), css_class="col-lg-6"),
                css_class="row mb-0",
            ),
            Div(
                Div(FloatingField("author"), css_class="col-lg-6"),
                Div(FloatingField("date_after"), css_class="col-lg-2"),
                Div(FloatingField("date_before"), css_class="col-lg-2"),
                Div(FloatingField("ordering"), css_class="col-lg-2"),
                css_class="row mb-0",
            ),
            Div(FloatingField("orderby"), css_class="d-none"),
        )

    def filter_queryset(
        self, queryset: "QuerySet[Submission]"
    ) -> "QuerySet[Submission]":
        if self.acad_field_slug and self.acad_field_slug != "all":
            queryset = queryset.filter(acad_field__slug=self.acad_field_slug)
        if self.specialty_slug and self.specialty_slug != "all":
            queryset = queryset.filter(specialties__slug=self.specialty_slug)
        if submitted_to := self.cleaned_data.get("submitted_to"):
            queryset = queryset.filter(submitted_to=submitted_to)
        if proceedings := self.cleaned_data.get("proceedings"):
            queryset = queryset.filter(proceedings=proceedings)
        if author := self.cleaned_data.get("author"):
            queryset = queryset.filter(author_list__icontains=author)
        if title := self.cleaned_data.get("title"):
            queryset = queryset.filter(title__icontains=title)
        if identifier := self.cleaned_data.get("identifier"):
            queryset = queryset.filter(
                preprint__identifier_w_vn_nr__icontains=identifier
            )
        if date_after := self.cleaned_data.get("date_after"):
            queryset = queryset.filter(submission_date__date__gte=date_after)
        if date_before := self.cleaned_data.get("date_before"):
            queryset = queryset.filter(submission_date__date__lte=date_before)

        return queryset


class PortalSubmissionNeedingReportsSearchForm(PortalSubmissionSearchForm):
    def filter_queryset(self, queryset: QuerySet[Submission]) -> QuerySet[Submission]:
        qs = super().filter_queryset(queryset)
        return qs.in_refereeing().open_for_reporting().reports_needed()


class SubmissionPoolSearchForm(CrispyFormMixin, SearchForm[Submission]):
    model = Submission

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
    title = forms.CharField(max_length=512, required=False)
    identifier = forms.CharField(max_length=128, required=False)
    status = forms.ChoiceField(choices=())
    editor_in_charge = forms.ModelChoiceField(
        queryset=Fellowship.objects.active().select_related("contributor__dbuser"),
        required=False,
    )

    hide_fully_appraised = forms.BooleanField(
        label="Hide fully appraised",
        required=False,
        initial=True,
    )
    hide_unqualified_for = forms.BooleanField(
        label="Hide unqualified for",
        required=False,
        initial=False,
    )

    orderby = forms.ChoiceField(
        label="Order by",
        choices=(
            ("assignment_deadline,submission_date", "Assignment deadline"),
            ("submission_date", "Submission date"),
            ("latest_activity", "Latest activity"),
        ),
        required=False,
        initial="assignment_deadline",
    )

    versions = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=(
            ("latest", "Latest submitted only"),
            ("any", "All versions"),
        ),
        initial="latest",
    )
    search_set = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=(
            ("current", "Currently under consideration"),
            (
                "current_noawaitingresub",
                "Currently under consideration\n(excluding awaiting resubmission)",
            ),
            ("historical", "All accessible history"),
        ),
        initial="current",
    )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        self.user = request.user
        super().__init__(*args, **kwargs)
        self.fields["status"].choices = self.get_status_choices(self.user)
        if not self.user.contributor.is_ed_admin:
            # restrict journals to those of Colleges of user's Fellowships
            self.fields["submitted_to"].queryset = Journal.objects.filter(
                college__in=self.user.contributor.fellowships.active().values("college")
            )

    def get_form_layout(self) -> Layout:
        div_block_checkbox = Div(
            Div(
                Field("hide_fully_appraised"),
                css_class="col-auto col-lg-12 col-xl-auto",
            ),
            Div(
                Field("hide_unqualified_for"),
                css_class="col-auto col-lg-12 col-xl-auto",
            ),
            css_class="row mb-0",
        )

        div_block_ordering = Div(
            Div(FloatingField("orderby"), css_class="col-6 col-md-12 col-xl-6"),
            Div(FloatingField("ordering"), css_class="col-6 col-md-12 col-xl-6"),
            css_class="row mb-0",
        )

        return Layout(
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
            Div(
                Div(Field("versions"), css_class="col"),
                Div(Field("search_set"), css_class="col"),
                Div(div_block_ordering, div_block_checkbox, css_class="col"),
                css_class="row mb-0",
            ),
        )

    @staticmethod
    def get_status_choices(user):
        incoming = (
            "Incoming",
            (
                (Submission.INCOMING, "Incoming: awaiting EdAdmin checks"),
                (Submission.ADMISSION_FAILED, "Admission failed"),
                (
                    Submission.ADMISSIBLE,
                    "Admissible; undergoing plagiarism checks",
                ),
                (
                    "plagiarism_internal_failed_temporary",
                    "Failed internal plagiarism checks (temporary)",
                ),
                (
                    "plagiarism_internal_failed_permanent",
                    "Failed internal plagiarism checks (permanent)",
                ),
                (
                    "plagiarism_iThenticate_failed_temporary",
                    "Failed iThenticate plagiarism checks (temporary)",
                ),
                (
                    "plagiarism_iThenticate_failed_permanent",
                    "Failed iThenticate plagiarism checks (permanent)",
                ),
            ),
        )
        preassignment = (
            "Preassignment",
            (
                (Submission.PREASSIGNMENT, "In preassignment"),
                (Submission.PREASSIGNMENT_FAILED, "preassignment failed"),
            ),
        )
        assignment = (
            "Assignment",
            (
                (Submission.SEEKING_ASSIGNMENT, "Seeking editor assignment"),
                ("assignment_1", "... waiting for > 1 week"),
                ("assignment_2", "... waiting for > 2 weeks"),
                ("assignment_4", "... waiting for > 4 weeks"),
                (
                    Submission.ASSIGNMENT_FAILED,
                    "Failed to find Editor-in-charge; manuscript rejected",
                ),
            ),
        )
        refereeing = (
            "Refereeing",
            (
                (
                    Submission.REFEREEING_IN_PREPARATION,
                    "Refereeing in preparation (cycle choice needed)",
                ),
                (
                    "in_preparation_week_1",
                    "... & inactive for > 1 week",
                ),
                ("in_refereeing", "In refereeing"),
                ("unvetted_reports", "... with unvetted Reports"),
                ("deadline_passed", "deadline passed, no recommendation yet"),
                ("refereeing_1", "Refereeing round ongoing for > 1 month"),
                ("refereeing_2", "Refereeing round ongoing for > 2 months"),
                ("refereeing_3", "Refereeing round ongoing for > 3 months"),
            ),
        )
        awaiting_resubmission = (
            "Awaiting resubmission",
            (
                (
                    Submission.AWAITING_RESUBMISSION,
                    "Awaiting resubmission (minor or major revision requested)",
                ),
            ),
        )
        voting = (
            "Voting",
            (
                ("voting_prepare", "Voting in preparation"),
                ("voting_ongoing", "Voting ongoing"),
                ("voting_1", "... in voting for > 1 week"),
                ("voting_2", "... in voting for > 2 weeks"),
                ("voting_4", "... in voting for > 4 weeks"),
                ("nr_voted_for_gte_4", "At least 4 votes cast in favour of EiC rec"),
            ),
        )
        decided = (
            "Decided",
            (
                (Submission.ACCEPTED_IN_TARGET, "Accepted in target Journal"),
                (
                    Submission.ACCEPTED_IN_ALTERNATIVE_AWAITING_PUBOFFER_ACCEPTANCE,
                    "Accepted in other journal; awaiting puboffer acceptance",
                ),
                (Submission.ACCEPTED_IN_ALTERNATIVE, "Accepted in alternative Journal"),
                (Submission.PUBLISHED, "Published"),
                (Submission.REJECTED, "Rejected"),
                (Submission.WITHDRAWN, "Withdrawn by the Authors"),
            ),
        )
        if user.contributor.is_ed_admin:
            choices = (
                ("All", (("all", "All Submissions"),)),
                incoming,
                preassignment,
                assignment,
                refereeing,
                awaiting_resubmission,
                voting,
                decided,
            )
        elif user.contributor.is_active_senior_fellow:
            choices = (
                ("All", (("all", "All Submissions"),)),
                preassignment,
                assignment,
                refereeing,
                awaiting_resubmission,
                voting,
                decided,
            )
        else:
            choices = (
                ("All", (("all", "All Submissions"),)),
                assignment,
                refereeing,
                awaiting_resubmission,
                voting,
                decided,
            )

        return choices

    def filter_queryset(
        self, queryset: "QuerySet[Submission]"
    ) -> "QuerySet[Submission]":
        versions = self.cleaned_data.get("versions")
        search_set = self.cleaned_data.get("search_set")

        queryset = queryset.in_pool(
            self.user,
            latest=versions == "latest",
            historical=search_set == "historical",
        )

        # Warning: this will only work for one fellowship per user
        fellowship: "Fellowship | None" = (
            self.user.contributor.fellowships.active().first()
        )
        if fellowship and self.cleaned_data.get("hide_fully_appraised"):
            queryset = (
                queryset.all()
                .annot_fully_appraised_by(fellowship.contributor)
                .exclude(is_fully_appraised=True)
            )
        if fellowship and self.cleaned_data.get("hide_unqualified_for"):
            queryset = queryset.exclude_not_qualified_for_fellow(fellowship.contributor)

        if not self.user.contributor.is_ed_admin:
            queryset = queryset.stage_incoming_completed()
        #     if not user.contributor.is_active_senior_fellow:
        #         queryset = queryset.stage_preassignment_completed()
        if search_set == "current_noawaitingresub":
            queryset = queryset.exclude(status=Submission.AWAITING_RESUBMISSION)
        if specialties := self.cleaned_data.get("specialties"):
            queryset = queryset.filter(specialties__in=specialties)
        if submitted_to := self.cleaned_data.get("submitted_to"):
            queryset = queryset.filter(submitted_to=submitted_to)
        if proceedings := self.cleaned_data.get("proceedings"):
            queryset = queryset.filter(proceedings=proceedings)
        if author := self.cleaned_data.get("author"):
            queryset = queryset.filter(author_list__unaccent__icontains=author)
        if title := self.cleaned_data.get("title"):
            queryset = queryset.filter(title__unaccent__icontains=title)
        if identifier := self.cleaned_data.get("identifier"):
            queryset = queryset.filter(
                preprint__identifier_w_vn_nr__icontains=identifier
            )

        # filter by status
        status = self.cleaned_data.get("status")
        if status == "all":
            pass
        elif status == "plagiarism_internal_failed_temporary":
            queryset = queryset.filter(
                internal_plagiarism_assessment__status=PlagiarismAssessment.STATUS_FAILED_TEMPORARY,
            )
        elif status == "plagiarism_internal_failed_permanent":
            queryset = queryset.filter(
                internal_plagiarism_assessment__status=PlagiarismAssessment.STATUS_FAILED_PERMANENT,
            )
        elif status == "plagiarism_iThenticate_failed_temporary":
            queryset = queryset.filter(
                iThenticate_plagiarism_assessment__status=PlagiarismAssessment.STATUS_FAILED_TEMPORARY,
            )
        elif status == "plagiarism_iThenticate_failed_permanent":
            queryset = queryset.filter(
                iThenticate_plagiarism_assessment__status=PlagiarismAssessment.STATUS_FAILED_PERMANENT,
            )
        elif status == "assignment_1":
            queryset = queryset.filter(
                status=Submission.SEEKING_ASSIGNMENT,
                submission_date__lt=timezone.now() - datetime.timedelta(days=7),
            )
        elif status == "assignment_2":
            queryset = queryset.filter(
                status=Submission.SEEKING_ASSIGNMENT,
                submission_date__lt=timezone.now() - datetime.timedelta(days=14),
            )
        elif status == "assignment_4":
            queryset = queryset.filter(
                status=Submission.SEEKING_ASSIGNMENT,
                submission_date__lt=timezone.now() - datetime.timedelta(days=28),
            )
        elif status == "in_refereeing":
            queryset = queryset.in_refereeing()
        elif status == "unvetted_reports":
            queryset = queryset.filter(
                id__in=Report.objects.awaiting_vetting().values("submission_id")
            )
        elif status == "deadline_passed":
            queryset = (
                queryset.in_refereeing()
                .filter(
                    reporting_deadline__isnull=False,
                    reporting_deadline__lt=timezone.now(),
                )
                .exclude(eicrecommendations__isnull=False)
            )
        elif status == "in_preparation_week_1":
            queryset = queryset.filter(
                status="refereeing_in_preparation",
                latest_activity__lt=timezone.now() - datetime.timedelta(days=7),
            )
        elif status == "refereeing_1":
            queryset = (
                queryset.filter(
                    referee_invitations__date_invited__lt=(
                        timezone.now() - datetime.timedelta(days=30)
                    )
                )
                .exclude(
                    referee_invitations__date_invited__lt=(
                        timezone.now() - datetime.timedelta(days=60)
                    )
                )
                .distinct()
                .exclude(eicrecommendations__isnull=False)
            )
        elif status == "refereeing_2":
            queryset = (
                queryset.filter(
                    referee_invitations__date_invited__lt=(
                        timezone.now() - datetime.timedelta(days=60)
                    )
                )
                .exclude(
                    referee_invitations__date_invited__lt=(
                        timezone.now() - datetime.timedelta(days=90)
                    )
                )
                .distinct()
                .exclude(eicrecommendations__isnull=False)
            )
        elif status == "refereeing_3":
            queryset = (
                queryset.filter(
                    referee_invitations__date_invited__lt=(
                        timezone.now() - datetime.timedelta(days=90)
                    )
                )
                .distinct()
                .exclude(eicrecommendations__isnull=False)
            )
        elif status == "voting_prepare":
            queryset = queryset.voting_in_preparation()
        elif status == "voting_ongoing":
            queryset = queryset.undergoing_voting()
        elif status == "voting_1":
            queryset = queryset.undergoing_voting(longer_than_days=7)
        elif status == "voting_2":
            queryset = queryset.undergoing_voting(longer_than_days=14)
        elif status == "voting_4":
            queryset = queryset.undergoing_voting(longer_than_days=28)
        elif status == "nr_voted_for_gte_4":
            queryset = queryset.undergoing_voting().filter(
                id__in=EICRecommendation.objects.put_to_voting()
                .annotate(nr_voted_for=Count("voted_for"))
                .filter(nr_voted_for__gte=4)
                .values_list("submission__id", flat=True)
            )
        else:  # if an actual unmodified status is used, just filter on that
            queryset = queryset.filter(status=status)

        # filter by EIC
        if eic := self.cleaned_data.get("editor_in_charge"):
            queryset = queryset.filter(editor_in_charge=eic.contributor)

        return queryset


class ReportSearchForm(CrispyFormMixin, SearchForm[Report]):
    model = Report
    queryset = Report.objects.accepted()

    submission_title = forms.CharField(max_length=100, required=False)

    def __init__(self, *args, **kwargs):
        self.acad_field_slug = kwargs.pop("acad_field_slug")
        self.specialty_slug = kwargs.pop("specialty_slug")
        super().__init__(*args, **kwargs)

    def get_form_layout(self) -> Layout:
        return Layout(Div(Div(FloatingField("submission_title"), css_class="col")))

    def filter_queryset(self, queryset: "QuerySet[Report]") -> "QuerySet[Report]":
        if self.acad_field_slug and self.acad_field_slug != "all":
            queryset = queryset.filter(
                submission__acad_field__slug=self.acad_field_slug
            )
        if self.specialty_slug and self.specialty_slug != "all":
            queryset = queryset.filter(
                submission__specialties__slug=self.specialty_slug
            )
        if sub_title := self.cleaned_data.get("submission_title"):
            queryset = queryset.filter(submission__title__icontains=sub_title)
        return queryset


# Marked for deprecation
class SubmissionOldSearchForm(forms.Form):
    """Filter a Submission queryset using basic search fields."""

    author = forms.CharField(max_length=100, required=False, label="Author(s)")
    title = forms.CharField(max_length=100, required=False)
    abstract = forms.CharField(max_length=1000, required=False)

    def search_results(self):
        """Return all Submission objects according to search."""
        return Submission.objects.public_latest().filter(
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
        if submission.status == Submission.REJECTED:
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
    `doi` is the DOI of the preprint, but can also be a link to the submission, or its database ID.
    """
    caller = ChemRxivCaller(doi)
    if not caller.is_valid or not (data := caller.data):
        error_message = (
            "The preprint could not be found. Please check the provided identifier."
        )
        raise forms.ValidationError(error_message)

    # Explicitly add ChemRxiv as the preprint server:
    data["preprint_server"] = PreprintServer.objects.get(name="ChemRxiv")
    return data, caller.metadata, data.get("identifier_w_vn_nr")


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
        if self.latest_submission:
            form_data["thread_hash"] = self.thread_hash
            form_data["is_resubmission_of"] = self.latest_submission.id
            form_data["proceedings"] = self.latest_submission.proceedings
            form_data["collection"] = self.latest_submission.collections.first()
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
                    "fulfilled_expectations": self.latest_submission.fulfilled_expectations,
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
                    "fulfilled_expectations": self.latest_submission.fulfilled_expectations,
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
        regex=ChemRxivCaller.valid_patterns,
        strip=True,
        error_messages={"invalid": "Invalid ChemRxiv DOI"},
        widget=forms.TextInput(),
    )

    def __init__(self, *args, **kwargs):
        self.data = {}
        self.metadata = {}
        super().__init__(*args, **kwargs)

    def clean_chemrxiv_doi(self):
        # To get the identifier, strip the DOI prefix
        identifier = self.cleaned_data.get("chemrxiv_doi", None).partition("/")[2]

        check_identifier_is_unused(identifier)
        self.data, self.metadata, identifier = check_chemrxiv_doi(
            self.cleaned_data["chemrxiv_doi"]
        )
        return identifier

    def get_prefill_data(self):
        """
        Return dictionary to prefill `SubmissionForm`.
        """
        form_data = super().get_prefill_data()
        form_data.update(self.data)

        # check metadata for specialties
        category_titles = (
            [c["name"].title() for c in self.metadata["categories"]]
            if self.metadata
            else []
        )
        form_data["specialties"] = Specialty.objects.filter(name__in=category_titles)

        # check keywords for topics
        keyword_titles = (
            [k.title() for k in self.metadata["keywords"]] if self.metadata else []
        )
        form_data["topics"] = Topic.objects.filter(name__in=keyword_titles)

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
                    "fulfilled_expectations": self.latest_submission.fulfilled_expectations,
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
                    "fulfilled_expectations": self.latest_submission.fulfilled_expectations,
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
                    "fulfilled_expectations": self.latest_submission.fulfilled_expectations,
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

    required_css_class = "required-asterisk"

    collection = forms.ChoiceField(
        choices=[(None, "-" * 9)],
        help_text="If your target collection is missing, please contact techsupport.",
        required=False,
    )
    specialties = forms.ModelMultipleChoiceField(
        queryset=Specialty.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url="/ontology/specialty-autocomplete", attrs={"data-html": True}
        ),
        label="Specialties",
        help_text="Type to search, click to include",
    )
    topics = forms.ModelMultipleChoiceField(
        queryset=Topic.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url="/ontology/topic-autocomplete",
            attrs={"data-html": True},
            forward=[
                "specialties",
            ],
        ),
        help_text="Type to search, click to include",
        required=False,
    )
    followup_of = forms.ModelMultipleChoiceField(
        queryset=Publication.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url="/journals/own-publication-autocomplete",
            attrs={
                "data-html": True,
                "data-placeholder": "Optional",
            },
        ),
        required=False,
        help_text="If this Submission follows up on some of your earlier publications, e.g. this Submission is a new release for a previous Codebases publication, select it here.<br>"
        "<strong>This is NOT FOR SPECIFYING A RESUBMISSION</strong>: to resubmit a manuscript, choose the resubmission route after clicking the Submit button in the navbar.",
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
        ),
        required=True,
    )

    code_name = forms.CharField(
        label="Software name",
        help_text="Name of the software referenced in this submission.",
        required=True,
    )
    code_version = forms.CharField(
        label="Software version",
        help_text="Software version referenced in this submission.",
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "v1.2.10, 2021.04, ..."}),
    )
    code_license = forms.CharField(
        label="Software license",
        help_text=(
            'License must be approved by <a href="https://opensource.org/licenses">OSI</a>. '
            + 'Consult <a href="https://scipost.org/SciPostPhysCodeb/about#licensing">the about page</a> for more information.'
        ),
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "AGPL-3.0, MIT, ..."}),
    )
    code_repository_url = forms.URLField(
        label="Code repository URL",
        required=False,
        widget=forms.URLInput(attrs={"placeholder": "https://..."}),
    )
    data_repository_url = forms.URLField(
        label="Data repository URL",
        required=False,
        widget=forms.URLInput(attrs={"placeholder": "https://..."}),
    )

    fulfilled_expectations = forms.MultipleChoiceField(
        choices=[],
        label="Fulfilled expectations",
        widget=forms.CheckboxSelectMultiple(),
    )

    class Meta:
        model = Submission
        fields = [
            "fulfilled_expectations",
            "is_resubmission_of",
            "thread_hash",
            "submitted_to",
            "proceedings",
            "collection",
            "acad_field",
            "specialties",
            "topics",
            "approaches",
            "title",
            "author_list",
            "abstract",
            "followup_of",
            "author_comments",
            "list_of_changes",
            "remarks_for_editors",
            "data_repository_url",
            "code_repository_url",
            "code_name",
            "code_version",
            "code_license",
            "preprint_file",
        ]
        widgets = {
            "submitted_to": forms.HiddenInput(),
            "acad_field": forms.HiddenInput(),
            "is_resubmission_of": forms.HiddenInput(),
            "thread_hash": forms.HiddenInput(),
            "remarks_for_editors": forms.Textarea(
                attrs={
                    "placeholder": "Optional: any private remarks (for the editors only)",
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

        if (
            (preprint_server := kwargs["initial"].get("preprint_server", None))
            or (preprint_server_id := data.get("preprint_server"))
            and (
                preprint_server := PreprintServer.objects.filter(
                    id=preprint_server_id
                ).first()
            )
        ):
            self.preprint_server = preprint_server
        else:
            raise ValueError("No preprint server specified.")

        self.thread_hash = kwargs["initial"].get("thread_hash", None) or data.get(
            "thread_hash"
        )
        self.is_resubmission_of = kwargs["initial"].get(
            "is_resubmission_of", None
        ) or data.get("is_resubmission_of")
        self.preprint_data = {}
        self.metadata = {}  # container for possible external server-provided metadata

        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        active_collections_in_journal = (
            Collection.objects.all()
            .annotate(
                contained_in_journal=Exists(
                    Journal.objects.filter(
                        id=self.submitted_to_journal.id,
                        contained_series__collections__in=OuterRef("id"),
                    )
                )
            )
            .filter(is_active=True, contained_in_journal=True)
            .order_by("-event_start_date")
        )

        self.fields["collection"].choices += list(
            active_collections_in_journal.annotate(
                name_with_series=Concat("series__name", Value(" - "), "name")
            ).values_list("id", "name_with_series")
        )

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

        object_types = self.submitted_to_journal.submission_object_types["options"]

        def require_type(str):
            """Check if a publishable object type is required for this journal."""
            return map(lambda x: str in x, object_types)

        # Define field option flags
        code_allowed = any(require_type(PUBLISHABLE_OBJECT_TYPE_CODEBASE))
        code_required = all(require_type(PUBLISHABLE_OBJECT_TYPE_CODEBASE))
        data_allowed = any(require_type(PUBLISHABLE_OBJECT_TYPE_DATASET))
        data_required = all(require_type(PUBLISHABLE_OBJECT_TYPE_DATASET))
        proceedings_allowed = "Proc" in self.submitted_to_journal.doi_label
        proceedings_required = proceedings_allowed
        collection_allowed = len(active_collections_in_journal) > 0
        collection_required = False
        expectations_allowed = self.submitted_to_journal.doi_label == "SciPostPhys"
        expectations_required = expectations_allowed

        # Mandate special submission fields if required by the journal
        if code_required:
            self.fields["code_repository_url"].required = True
        else:
            del self.fields["code_name"]
            del self.fields["code_version"]
            del self.fields["code_license"]

        self.fields["data_repository_url"].required = data_required
        self.fields["collection"].required = collection_required
        self.fields["proceedings"].required = proceedings_required

        # Delete special submission fields if not allowed by the journal
        if not code_allowed:
            del self.fields["code_repository_url"]

        if not data_allowed:
            del self.fields["data_repository_url"]

        if not collection_allowed:
            del self.fields["collection"]

        if not proceedings_allowed:
            del self.fields["proceedings"]
        else:
            # Filter the list of proceedings to those open for submission
            proceedings_qs = self.fields["proceedings"].queryset.open_for_submission()

            # If this is a resubmission, add the previous proceedings to the list
            if self.is_resubmission():
                resubmission = Submission.objects.get(id=self.is_resubmission_of)
                if resubmission.proceedings:
                    proceedings_qs |= Proceedings.objects.filter(
                        id=resubmission.proceedings.id
                    )

            self.fields["proceedings"].queryset = proceedings_qs

        if not expectations_allowed:
            del self.fields["fulfilled_expectations"]
        else:
            self.fields["fulfilled_expectations"].help_text = (
                "<div class='mt-2'>Please indicate which <a href='{expectations_url}'>journal expectations</a> "
                "you assert are being fulfilled by this Submission."
                "At least one should be fulfilled for publication in {journal_name}. <br>"
                "This information will be publicly visible and scrutinized during the refereeing process. <br><br>"
                "Looking for a more accessible alternative? "
                "Consider <a href='{core_url}{thread_hash_get_param}'>submitting to {journal_name} Core</a>.</div>"
            ).format(
                expectations_url=reverse_lazy(
                    "journal:about", args=[self.submitted_to_journal.doi_label]
                )
                + "#criteria",
                journal_name=self.submitted_to_journal.name,
                core_url=reverse_lazy(
                    "submissions:submit_choose_preprint_server",
                    args=[self.submitted_to_journal.doi_label + "Core"],
                ),
                thread_hash_get_param=(
                    f"?thread_hash={self.thread_hash}" if self.thread_hash else ""
                ),
            )
            self.fields[
                "fulfilled_expectations"
            ].choices = self.submitted_to_journal.expectations

        def _no_fields_present(*fields: list[str]):
            """
            Check if all fields are missing (not present in self.fields).
            """
            return all([field not in self.fields for field in fields])

        is_expected_author_of_any_collection = (
            self.requested_by.contributor.profile.id
            in list(
                active_collections_in_journal.values_list("expected_authors", flat=True)
            )
        )

        collection_col = Div(
            Div(
                HTML(
                    '<div class="mb-3 text-muted fs-6">'
                    f"If your submission is part of a collection (e.g. {active_collections_in_journal.first()}), "
                    "please select it from the list.</div>"
                ),
                Field("collection"),
                css_class="p-2 bg-secondary bg-opacity-10"
                + (
                    " border border-warning border-2"
                    if is_expected_author_of_any_collection
                    else ""
                ),
            ),
            css_class="col-12 col-md-4",
        )

        # Remove entire collection block if collection field is missing
        if _no_fields_present("collection"):
            collection_col = None

        codebase_metadata_row = Div(
            Div(Field("code_name"), css_class="col-12 col-md"),
            Div(Field("code_version"), css_class="col-12 col-md-3"),
            Div(Field("code_license"), css_class="col-12 col-md"),
            css_class="row mb-0",
        )

        # Remove codebase metadata row if no fields are present
        if _no_fields_present("code_name", "code_version", "code_license"):
            codebase_metadata_row = None

        supp_info_fieldset = Fieldset(
            "Supplementary information",
            Div(
                HTML(
                    '<div class="mb-3 text-muted fs-6">Provide all reproducibility-enabling resources: '
                    "datasets and processing methods, processed data "
                    "and code snippets used to produce figures, etc.</div>"
                ),
                Field("data_repository_url"),
                Field("code_repository_url"),
                codebase_metadata_row,
                css_class="p-2 bg-secondary bg-opacity-10 mb-3",
            ),
        )

        # Remove supplementary information fieldset if no fields are present
        if _no_fields_present("data_repository_url", "code_repository_url"):
            supp_info_fieldset = None

        self.helper.layout = Layout(
            # Hidden fields
            "preprint_server",
            "preprint_link",
            "identifier_w_vn_nr",
            "submitted_to",
            "acad_field",
            "is_resubmission_of",
            "thread_hash",
            # Visible fields
            "fulfilled_expectations",
            "is_resubmission_of",
            "thread_hash",
            "submitted_to",
            "proceedings",
            "acad_field",
            Div(
                Div(
                    Field("specialties"),
                    Field("topics"),
                    Field("approaches"),
                    css_class="col-12 col-md",
                ),
                collection_col,
                css_class="row",
            ),
            "title",
            "author_list",
            "abstract",
            "followup_of",
            "author_comments",
            "list_of_changes",
            "remarks_for_editors",
            supp_info_fieldset,
            "preprint_file",
        )

    def is_resubmission(self):
        return self.is_resubmission_of is not None

    def clean(self, *args, **kwargs):
        """
        Do all general checks for Submission.
        """
        cleaned_data = super().clean(*args, **kwargs)

        self._clean_collection()

        # SciPost preprints are auto-generated here.
        if "identifier_w_vn_nr" not in cleaned_data:
            cleaned_data["identifier_w_vn_nr"] = get_new_scipost_identifier(
                thread_hash=self.thread_hash
            )

        if self.is_resubmission():
            check_resubmission_readiness(
                self.requested_by, cleaned_data["is_resubmission_of"]
            )

        self.clear_submission_object_types()

        if "Proc" not in cleaned_data["submitted_to"].doi_label:
            try:
                del self.cleaned_data["proceedings"]
            except KeyError:
                # No proceedings returned to data
                pass
        return cleaned_data

    def clear_submission_object_types(self):
        """
        Check that the submitted material fits one of the Journal's options.
        """
        submitted_types = []
        if preprint_file := self.cleaned_data.get("preprint_file"):
            submitted_types.append(PUBLISHABLE_OBJECT_TYPE_ARTICLE)

            # Check the file extension
            source_file_extensions = ["tex", "zip", "tar", "doc", "docx", "odf"]
            extension = preprint_file.name.split(".")[-1].lower()
            if extension != "pdf":
                error_message = "Please submit a .pdf file. "
                if extension in source_file_extensions:
                    error_message += "We ask for your source files upon acceptance."

                self.add_error("preprint_file", error_message)

        elif self.cleaned_data.get("preprint_link"):
            submitted_types.append(PUBLISHABLE_OBJECT_TYPE_ARTICLE)
        if self.cleaned_data.get("code_repository_url", None):
            submitted_types.append(PUBLISHABLE_OBJECT_TYPE_CODEBASE)
        if self.cleaned_data.get("data_repository_url", None):
            submitted_types.append(PUBLISHABLE_OBJECT_TYPE_DATASET)
        submitted_types.sort()  # not needed here, but for future safety
        submitted_types_code = " + ".join(submitted_types)
        options = self.cleaned_data["submitted_to"].submission_object_types["options"]
        if submitted_types_code not in options:
            self.add_error(
                None,
                (
                    f"You are trying to submit document types: {submitted_types_code}, "
                    "but this Journal requires one of the following options: "
                    f"{', '.join(options)}"
                ),
            )

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

    def _clean_collection(self):
        """
        Check that the collection is part of a series in the target journal and that
        at least one of the authors in the list is an expected author of the collection.
        """
        # Check if no collection is selected or fetch the object
        collection_id = self.cleaned_data.get("collection", "")
        if collection_id == "":
            return

        collection = get_object_or_404(Collection, id=collection_id)

        # Check that the collection is part of a series in the target journal
        if not self.submitted_to_journal in collection.series.container_journals.all():
            self.add_error(
                "collection",
                "This collection is not part of a series in the target journal. "
                "Please check that the collection and journal are correct before contacting techsupport.",
            )

        # Check that the author list is not empty
        str_author_list = self.cleaned_data.get("author_list", "")
        if str_author_list == "":
            self.add_error(
                "collection",
                "The author list is empty, so the collection may not be validated.",
            )

        # Check that the collection has defined expected authors
        if collection.enforce_expected_authors:
            listed_names = [name.strip() for name in str_author_list.split(",")]
            expected_names = [
                a.full_name.strip() for a in collection.expected_authors.all()
            ]
            if len(expected_names) == 0:
                self.add_error(
                    "collection",
                    "This collection has no specified authors yet, please contact techsupport.",
                )
            # Check that at least one of the authors in the list is an expected author of the collection
            elif not any(
                partial_names_match(listed, expected, symmetric=True)
                for listed, expected in product(listed_names, expected_names)
            ):
                self.add_error(
                    "collection",
                    "None of the authors in the author list match any of the expected authors of this collection. "
                    "Please check that the author list and collection are correct before contacting techsupport.",
                )

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

    def clean_title(self):
        return remove_extra_spacing(self.cleaned_data["title"])

    def clean_abstract(self):
        return remove_extra_spacing(self.cleaned_data["abstract"])

    @transaction.atomic
    def save(self):
        """
        Create the new Submission and Preprint instances.
        """
        submission: Submission = super().save(commit=False)
        submission.submitted_by = self.requested_by.contributor

        # Save expectations
        if fulfilled_expectations := self.cleaned_data.get("fulfilled_expectations"):
            submission.fulfilled_expectations = fulfilled_expectations

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

        # Metadata fields (optional)
        METADATA_FIELD_NAMES = [
            "code_name",
            "code_version",
            "code_license",
            "code_repository_url",
            "data_repository_url",
        ]
        submission.article_metadata |= {
            field_name: self.cleaned_data[field_name]
            for field_name in METADATA_FIELD_NAMES
            if field_name in self.cleaned_data
        }

        submission.save()
        submission.topics.add(*self.cleaned_data["topics"])

        # Try to match the submitting author's last name to a position from the author list.
        try:
            submitting_author_order = 1 + (
                [
                    submission.submitted_by.profile.last_name in author
                    for author in submission.author_list.split(",")
                ]
            ).index(True)
        except ValueError:
            # Otherwise, assume the submitting author is the first author.
            submitting_author_order = 1

        # Add the submitter's AuthorProfile:
        author_profile = SubmissionAuthorProfile(
            submission=submission,
            profile=self.requested_by.contributor.profile,
            order=submitting_author_order,
        )
        author_profile.save()

        # Explicitly handle specialties (otherwise they are not saved)
        submission.specialties.set(self.cleaned_data["specialties"])

        if self.is_resubmission():
            self.process_resubmission(submission)

        # Add the Collection if applicable
        if collection := self.cleaned_data.get("collection", None):
            submission.collections.add(collection)

        # Gather first known author and Fellows.
        submission.authors.add(self.requested_by.contributor)

        # Set the fellowship to the default one
        submission.fellows.set(submission.get_default_fellowship())
        if self.is_resubmission():
            # Add the fellows of the previous submission to the new one
            submission.fellows.add(*submission.is_resubmission_of.fellows.all())

        # Switch off auto-updating of the fellowship
        if collection or self.submitted_to_journal.name == "Migration Politics":
            submission.auto_update_fellowship = False

        # Return latest version of the Submission. It could be outdated by now.
        submission.refresh_from_db()
        return submission

    def process_resubmission(self, submission: Submission):
        """
        Update all fields for new and old Submission and EditorialAssignments.

        -- submission: the new version of the Submission series.
        """
        if not submission.is_resubmission_of:
            raise Submission.DoesNotExist

        previous_submission = submission.is_resubmission_of

        # Close last submission
        Submission.objects.filter(id=previous_submission.id).update(
            open_for_reporting=False, status=Submission.RESUBMITTED
        )

        # Copy related objects
        submission.topics.add(*previous_submission.topics.all())
        submission.collections.add(*previous_submission.collections.all())
        submission.followup_of.add(*previous_submission.followup_of.all())

        # Open for comments (reports: opened upon cycle choice) and copy EIC info
        Submission.objects.filter(id=submission.id).update(
            open_for_commenting=True,
            open_for_reporting=False,
            visible_public=previous_submission.visible_public,
            visible_pool=True,
            refereeing_cycle=CYCLE_UNDETERMINED,
            editor_in_charge=previous_submission.editor_in_charge,
            status=Submission.REFEREEING_IN_PREPARATION,
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
            status=EditorialAssignment.STATUS_ACCEPTED,
        )

        # Set author-profile relations to those of the previous submission
        submission.author_profiles.all().delete()
        previous_profiles = list(previous_submission.author_profiles.all())
        for author_profile in previous_profiles:
            author_profile.pk = None
            author_profile.submission = submission
        SubmissionAuthorProfile.objects.bulk_create(previous_profiles)


class SubmissionReportsForm(forms.ModelForm):
    """Update refereeing pdf for Submission."""

    class Meta:
        model = Submission
        fields = ["pdf_refereeing_pack"]


class PreassignEditorsForm(forms.ModelForm):
    """Preassign editors during Submission preassignment."""

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
            if self.instance.status == Submission.PREASSIGNED:
                self.instance.delete()
        return self.instance

    def get_fellow(self):
        """Get fellow either via initial data or instance."""
        if self.instance.id is not None:
            return self.instance.to
        return self.initial.get("to", None)


class BasePreassignEditorsFormSet(forms.BaseModelFormSet):
    """Pre-assign editors during Submission preassignment."""

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
    email_old_eic = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Whether the previous EiC should be informed",
    )

    class Meta:
        model = Submission
        fields = ()

    def __init__(self, *args, **kwargs):
        """Add related submission as argument."""
        self.submission: "Submission" = kwargs.pop("submission")
        super().__init__(*args, **kwargs)

        self.fields["new_editor"].queryset = Contributor.objects.filter(
            fellowships__in=self.submission.fellows.all()
        ).exclude(id=self.submission.editor_in_charge.id)

    def save(self):
        """Update old/create new Assignment and send mails."""
        assignment, old_assignment = self.submission.set_editor_in_charge(
            self.cleaned_data["new_editor"]
        )

        # Email old and new editor for the change in the latest submission
        if old_assignment and self.cleaned_data["email_old_eic"]:
            mail_sender = DirectMailUtil(
                "fellows/email_fellow_replaced_by_other", assignment=old_assignment
            )
            mail_sender.send_mail()

        if assignment:
            mail_sender = DirectMailUtil(
                "fellows/email_fellow_assigned_submission", assignment=assignment
            )
            mail_sender.send_mail()

        # Also update the editor for all other versions without sending mails
        for submission in self.submission.get_other_versions():
            submission.set_editor_in_charge(self.cleaned_data["new_editor"])


class SubmissionTargetJournalForm(forms.ModelForm):
    """Change the target journal for the Submission."""

    keep_manually_added_fellows = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Keep manually added fellows from the previous journal's college.",
    )

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
            Field("keep_manually_added_fellows"),
            ButtonHolder(Submit("submit", "Update", css_class="btn btn-danger")),
        )

    def clean_submitted_to(self):
        journal = self.cleaned_data["submitted_to"]
        if journal == self.instance.submitted_to:
            raise forms.ValidationError(
                "The target journal must be different than the current one."
            )
        return journal

    def save(self):
        self.instance: Submission

        self.instance.set_target_journal(
            self.cleaned_data["submitted_to"],
            self.cleaned_data["keep_manually_added_fellows"],
        )
        self.instance.fulfilled_expectations = ""
        self.instance.save()

        return self.instance


class SubmissionTargetProceedingsForm(forms.ModelForm):
    """Change the target Proceedings for the Submission."""

    keep_manually_added_fellows = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Keep manually added fellows from the previous journal's college.",
    )

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
            Field("keep_manually_added_fellows"),
            ButtonHolder(Submit("submit", "Update", css_class="btn btn-danger")),
        )

    def save(self):
        proceedings = self.cleaned_data["proceedings"]
        keep_fellows = self.cleaned_data["keep_manually_added_fellows"]

        self.instance.set_target_proceedings(proceedings, keep_fellows)


class SubmissionCollectionsForm(forms.ModelForm):
    """Change the target Collections for the Submission."""

    class Meta:
        model = Submission
        fields = []

    collections = forms.ModelMultipleChoiceField(
        queryset=Collection.objects.all(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["collections"].initial = self.instance.collections.all()

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("collections"),
            ButtonHolder(Submit("submit", "Update", css_class="btn btn-danger")),
        )

    def save(self):
        """Update the target Collections for the Submission."""
        self.instance.collections.set(self.cleaned_data["collections"])


class SubmissionPreprintFileForm(forms.ModelForm):
    """Change the submitted pdf for the Submission."""

    _file = forms.FileField(
        help_text=("Simply submit the new .pdf file, the old one will be replaced."),
        required=True,
    )

    class Meta:
        model = Preprint
        fields = ["_file"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("_file"),
            ButtonHolder(Submit("submit", "Update", css_class="btn btn-danger")),
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
                status=Submission.WITHDRAWN,
                assignment_deadline=None,
                latest_activity=timezone.now(),
            )
            self.submission.get_other_versions().update(visible_public=False)

            # Update all assignments
            EditorialAssignment.objects.filter(
                submission__thread_hash=self.submission.thread_hash
            ).need_response().update(status=EditorialAssignment.STATUS_DEPRECATED)
            EditorialAssignment.objects.filter(
                submission__thread_hash=self.submission.thread_hash
            ).accepted().update(status=EditorialAssignment.STATUS_COMPLETED)

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
    refusal_reason = forms.ChoiceField(choices=EditorialAssignment.REFUSAL_REASONS)

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
                # Update related Submission.
                Submission.objects.filter(id=self.submission.id).update(
                    refereeing_cycle=CYCLE_DEFAULT,
                    status=Submission.IN_REFEREEING,
                    editor_in_charge=self.request.user.contributor,
                    reporting_deadline=None,
                    assignment_deadline=None,
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
                    status=Submission.REFEREEING_CLOSED,
                    editor_in_charge=self.request.user.contributor,
                    reporting_deadline=timezone.now(),
                    assignment_deadline=None,
                    open_for_reporting=False,
                    open_for_commenting=True,
                    visible_public=visible_public,
                    latest_activity=timezone.now(),
                )
                # Refresh the instance
                self.instance.submission = Submission.objects.get(id=self.submission.id)

            # Implicitly or explicity accept the assignment and deprecate others.
            assignment.status = EditorialAssignment.STATUS_ACCEPTED

            # Update all other 'open' invitations
            EditorialAssignment.objects.filter(
                submission=self.submission
            ).need_response().exclude(id=assignment.id).update(
                status=EditorialAssignment.STATUS_DEPRECATED,
            )

            # Decline all standing ConditionalAssignments
            self.instance.submission.conditional_assignment_offers.offered().update(
                status=ConditionalAssignmentOffer.STATUS_DECLINED
            )
        else:
            assignment.status = EditorialAssignment.STATUS_DECLINED
            assignment.refusal_reason = self.cleaned_data["refusal_reason"]
        assignment.save()  # Save again to register acceptance
        return assignment


class InviteRefereeSearchForm(CrispyFormMixin, SearchForm[Profile]):
    model = Profile
    queryset = Profile.objects.eponymous()
    form_id = "invite-referee-search-form"

    text = forms.CharField(
        required=False, help_text="Fill in a name, email or ORCID", label="Search"
    )
    affiliation = forms.CharField(required=False)
    specialties = forms.MultipleChoiceField(
        choices=[],
        label="Submission specialties",
        required=False,
    )

    hide_unavailable = forms.BooleanField(
        required=False,
        initial=False,
        label="Hide unavailable",
    )
    hide_with_CoI = forms.BooleanField(
        required=False,
        initial=False,
        label="Hide those with conflicts of interest",
    )
    show_email_unknown = forms.BooleanField(
        required=False,
        initial=True,
        label="Show without email",
    )

    orderby = forms.ChoiceField(
        label="Order by",
        choices=[
            ("last_name,first_name", "Last Name"),
            ("first_name,last_name", "First Name"),
        ],
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.submission = kwargs.pop("submission")
        self.session_key = kwargs.pop("session_key", None)
        super().__init__(*args, **kwargs)

        self.fields[
            "specialties"
        ].choices = self.submission.specialties.all().values_list("id", "name")

    def get_form_layout(self) -> Layout:
        div_block_ordering = Div(
            Div(Field("orderby"), css_class="col-6"),
            Div(Field("ordering"), css_class="col-6"),
            css_class="row mb-0",
        )
        div_block_options = Div(
            Div(Field("hide_unavailable"), css_class="col-auto"),
            Div(Field("hide_with_CoI"), css_class="col-auto"),
            Div(Field("show_email_unknown"), css_class="col-auto"),
            css_class="row mb-0",
        )

        return Layout(
            Div(
                Div(
                    Div(
                        Div(FloatingField("text"), css_class="col-12 mb-2"),
                        Div(FloatingField("affiliation"), css_class="col-12"),
                        css_class="row mb-0 d-flex flex-column justify-content-between h-100",
                    ),
                    css_class="col",
                ),
                Div(
                    Field("specialties", size=6),
                    css_class="col-12 col-md-4",
                ),
                Div(
                    Div(
                        Div(div_block_options, css_class="col-12"),
                        Div(div_block_ordering, css_class="col-12"),
                        css_class="row mb-0 d-flex flex-column justify-content-between h-100",
                    ),
                    css_class="col-12 col-md",
                ),
                css_class="row mb-0",
            ),
        )

    def filter_queryset(self, queryset: QuerySet[Profile]) -> QuerySet[Profile]:
        queryset = queryset.annotate(
            last_name_matches=Exists(
                Submission.objects.filter(
                    id=self.submission.id,
                    author_list__unaccent__icontains=OuterRef("last_name"),
                )
            ),
            has_accepted_previous_invitation=Exists(
                RefereeInvitation.objects.filter(
                    referee=OuterRef("id"),
                    submission__thread_hash=self.submission.thread_hash,
                    accepted=True,
                ).exclude(submission=self.submission)
            ),
            already_invited=Exists(
                RefereeInvitation.objects.filter(
                    referee=OuterRef("id"),
                    submission=self.submission,
                    cancelled=False,
                )
            ),
            has_any_email=Exists(ProfileEmail.objects.filter(profile=OuterRef("id"))),
        )

        if text := self.cleaned_data.get("text"):
            queryset = queryset.search(text)

        if affiliation := self.cleaned_data.get("affiliation"):
            queryset = queryset.filter(
                affiliations__organization__name__icontains=affiliation
            )

        can_be_sent_invitation_expression = (
            Q(has_any_email=True)
            & ~Q(already_invited=True)
            & Q(accepts_refereeing_requests=True)
        )
        warned_against_invitation_expression = Q(id__isnull=True)

        # Filter to only those without conflicts of interest, if the option is selected
        if self.cleaned_data.get("hide_with_CoI"):
            can_be_sent_invitation_expression &= ~Q(
                has_any_conflict_of_interest_with_submission=True
            )
            warned_against_invitation_expression |= Q(is_submission_author=False) & Q(
                last_name_matches=True
            )

            queryset = (
                queryset.without_conflicts_of_interest_against_submission_authors_of(
                    self.submission,
                    purpose=CoauthorshipExclusionPurpose.REFEREEING,
                )
            )

        # Filter out unavailable referees if the option is selected
        if self.cleaned_data.get("hide_unavailable"):
            warned_against_invitation_expression |= Q(is_unavailable=True) & Q(
                has_accepted_previous_invitation=True
            )

            queryset = queryset.annotate(
                is_unavailable=Exists(
                    UnavailabilityPeriod.objects.today().filter(
                        contributor=OuterRef("contributor")
                    )
                )
            )
            queryset = queryset.exclude(is_unavailable=True)

        # Filter to only those with email, if the option is selected
        if not self.cleaned_data.get("show_email_unknown"):
            queryset = queryset.filter(has_any_email=True)

        if specialties := self.cleaned_data.get("specialties"):
            queryset = queryset.filter(specialties__in=specialties)

        queryset = queryset.annotate(
            can_be_sent_invitation=ExpressionWrapper(
                can_be_sent_invitation_expression,
                output_field=BooleanField(),
            ),
            warned_against_invitation=ExpressionWrapper(
                warned_against_invitation_expression,
                output_field=BooleanField(),
            ),
        )

        Q_last_5y = Q(
            referee_invitations__date_invited__gt=timezone.now()
            - timedelta(days=365 * 5),
        )
        # Add invitation statistics
        queryset = queryset.annotate(
            invitations_sent_5y=Count(
                "referee_invitations",
                filter=Q_last_5y,
            ),
            invitations_accepted_5y=Count(
                "referee_invitations",
                filter=Q_last_5y
                & Q(
                    referee_invitations__accepted=True,
                    referee_invitations__cancelled=False,
                    referee_invitations__fulfilled=False,
                ),
            ),
            invitations_declined_5y=Count(
                "referee_invitations",
                filter=Q_last_5y
                & Q(
                    referee_invitations__accepted=False,
                    referee_invitations__cancelled=False,
                ),
            ),
            invitations_fulfilled_5y=Count(
                "referee_invitations",
                filter=Q_last_5y
                & Q(
                    referee_invitations__fulfilled=True,
                    referee_invitations__cancelled=False,
                ),
            ),
            invitations_cancelled_5y=Count(
                "referee_invitations",
                filter=Q_last_5y & Q(referee_invitations__cancelled=True),
            ),
        )

        return queryset


class ConfigureRefereeInvitationForm(forms.Form):
    """
    Displayed when the EIC has selected a referee and wants to configure the invitation to be sent.
    Allows the selection of profile emails to send the invitation to, as well as invitation reminder parameters.
    """

    has_auto_reminders = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=((True, "Yes"), (False, "No")),
        initial=True,
        required=False,
        label="Send automatic reminders?",
    )
    profile_email = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=[],
        required=True,
        label="Email address",
    )

    def __init__(self, *args, **kwargs):
        """
        Add the list of available profile emails to the form.
        """
        self.submission = kwargs.pop("submission")
        self.profile: "Profile" = kwargs.pop("profile")
        super().__init__(*args, **kwargs)

        self.fields["profile_email"].choices = [
            (email.email, email.email) for email in self.profile.emails.all()
        ]
        self.fields["profile_email"].initial = self.profile.emails.first().email

        self.helper = FormHelper()
        self.helper.form_action = reverse(
            "submissions:_hx_customize_refereeing_invitation",
            kwargs={
                "identifier_w_vn_nr": self.submission.preprint.identifier_w_vn_nr,
                "profile_id": self.profile.id,
            },
        )
        self.helper.layout = Layout(
            Div(
                Div(
                    Field("has_auto_reminders"),
                    HTML(
                        '<span class="text-muted">Whether to remind the referee automatically '
                        '{% include "submissions/_refinv_auto_reminders_tooltip.html" %}</span>'
                    ),
                ),
                Div(Field("profile_email"), css_class="mx-4"),
                ButtonHolder(
                    Submit("submit", "Draft Email", css_class="btn btn-sm btn-primary"),
                    Button(
                        "cancel",
                        "Cancel",
                        css_class="btn btn-sm btn-secondary",
                        hx_get=reverse("common:empty"),
                        hx_target="closest tr",
                        hx_swap="outerHTML",
                    ),
                    css_class="d-flex flex-column justify-content-between",
                ),
                css_class="d-flex flex-row justify-content-center",
            )
        )


class ConsiderRefereeInvitationForm(forms.Form):
    accept = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=((True, "Accept"), (False, "Decline")),
        label="Are you willing to referee this Submission?",
    )
    intended_delivery_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Intended delivery date",
        help_text=("The date by which you intend to deliver your report."),
    )
    refusal_reason = forms.ChoiceField(
        choices=[(None, "-" * 9)] + list(EditorialAssignment.REFUSAL_REASONS),
        required=False,
    )
    other_refusal_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(
            {
                "placeholder": "Please shortly describe your reason for declining. (255 characters max)"
            }
        ),
        max_length=255,
    )

    def __init__(self, *args, **kwargs):
        self.invitation: "RefereeInvitation" = kwargs.pop("invitation", None)
        super().__init__(*args, **kwargs)

        if self.invitation is not None:
            self.fields["intended_delivery_date"].initial = (
                self.invitation.submission.reporting_deadline
                or self.invitation.submission.cycle.get_default_refereeing_deadline()
            ).date()

    def clean(self):
        accepted = self.cleaned_data.get("accept", None)
        intended_delivery_date = self.cleaned_data.get("intended_delivery_date", None)
        reason = self.cleaned_data.get("refusal_reason", "")
        other_refusal_reason = self.cleaned_data.get("other_refusal_reason", "")

        if accepted == "False":
            if reason == "":
                self.add_error(
                    "refusal_reason", "Please select a reason for declining."
                )
            if reason == "OTH" and other_refusal_reason == "":
                self.add_error(
                    "other_refusal_reason", "Please specify your reason for declining."
                )
            elif reason != "OTH" and other_refusal_reason != "":
                self.add_error(
                    "other_refusal_reason",
                    'Please select "Other" to specify your reason for declining.',
                )
        elif accepted == "True":
            if reason != "":
                self.add_error(
                    "refusal_reason",
                    "You cannot select a refusal reason if you accept.",
                )

            if intended_delivery_date is None:
                self.add_error(
                    "intended_delivery_date",
                    "Please select an intended delivery date for your report.",
                )

    def save(self, commit=True):
        accepted = self.cleaned_data.get("accept", None)
        intended_delivery_date = self.cleaned_data.get("intended_delivery_date", None)
        refusal_reason = self.cleaned_data.get("refusal_reason", None)
        other_refusal_reason = self.cleaned_data.get("other_refusal_reason", None)

        self.invitation.accepted = accepted
        self.invitation.intended_delivery_date = intended_delivery_date
        self.invitation.refusal_reason = refusal_reason
        self.invitation.other_refusal_reason = other_refusal_reason

        self.invitation.submission.add_event_for_eic(
            f"Referee {self.invitation.referee.full_name} set intended report delivery date to {self.invitation.intended_delivery_date}."
        )
        self.invitation.submission.add_event_for_author(
            f"A referee has set their intended report delivery date to {self.invitation.intended_delivery_date}."
        )

        if commit:
            self.invitation.save()

        return self.invitation


class RefereeInvitationChangeEmailForm(forms.ModelForm):
    """Form to change the email address of a RefereeInvitation."""

    reset_statistics = forms.BooleanField(
        required=False,
        initial=False,
        label="Reset invitation statistics",
        help_text="Reset the number of reminders sent and the date of last reminder.",
    )

    email_address = forms.ChoiceField()

    class Meta:
        model = RefereeInvitation
        fields = ["email_address"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email_address"].choices = [
            (email, email)
            for email in self.instance.referee.emails.values_list("email", flat=True)
        ]
        self.fields["email_address"].initial = self.instance.email_address

    def clean_email_address(self):
        email_address = self.cleaned_data["email_address"]
        if email_address == self.instance.email_address:
            raise forms.ValidationError(
                "Please select a different email address than the current one."
            )
        return email_address

    def save(self, commit=True):
        """
        Save the new email address to the RefereeInvitation,
        and reset any invitation statistics and counters.
        Create a submission event about the change.
        """
        self.instance.email_address = self.cleaned_data["email_address"]
        if reset_statistics := self.cleaned_data.get("reset_statistics", False):
            self.instance.nr_reminders = 0
            self.instance.date_last_reminded = None
            self.instance.date_invited = None
        if commit:
            self.instance.save()

        self.instance.submission.add_event_for_edadmin(
            f"Changed invitation email address for referee {self.instance.referee.full_name} to {self.instance.email_address}."
            + (" Reset invitation statistics." if reset_statistics else "")
        )
        return self.instance


class ReportIntendedDeliveryForm(forms.ModelForm):
    """
    Contrary to what may be assumed by its name, this is a model form for RefereeInvitation.
    It is used to set the intended delivery date for a referee's report, prior to the report being written.
    """

    class Meta:
        model = RefereeInvitation()
        fields = ["intended_delivery_date"]
        widgets = {
            "intended_delivery_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.attrs = {
            "hx-post": reverse_lazy(
                "submissions:_hx_report_intended_delivery_form",
                kwargs={"invitation_id": self.instance.id},
            ),
            "hx-target": "this",
        }
        self.helper.layout = Layout(
            Div(
                Field("intended_delivery_date"),
                ButtonHolder(
                    Submit("submit", "Save", css_class="btn btn-primary ms-2 mb-3")
                ),
                css_class="d-flex flex-row align-items-end",
            )
        )

    def save(self):
        super().save()

        self.instance.submission.add_event_for_eic(
            f"Referee {self.instance.referee.full_name} set intended report delivery date to {self.instance.intended_delivery_date}."
        )
        self.instance.submission.add_event_for_author(
            f"A referee has set their intended report delivery date to {self.instance.intended_delivery_date}."
        )

        return self.instance


class SetRefereeingDeadlineForm(forms.Form):
    deadline = forms.DateField(
        label="",
        widget=forms.DateInput(attrs={"type": "date"}),
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
            .order_by("dbuser__last_name")
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

    def get_eligible_fellows_and_their_coauthorships(self):
        return self.instance.submission.custom_prefetch_submission_author_and_contributor_coauthorships(
            self.fields["eligible_fellows"].queryset
        )


############
# Reports:
############


class ReportPDFForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["pdf_report"]


class ReportForm(forms.ModelForm):
    """Write Report form."""

    required_css_class = "required-asterisk"
    report_type = REPORT_NORMAL
    anonymity = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=[
            ("anonymous", "Publish report anonymously"),
            ("eponymous", "Publish report with name"),
        ],
    )
    license_agreement = forms.BooleanField(
        required=True,
        label="I agree for this report to be published under a CC BY 4.0 license.",
        help_text="The <a href='https://creativecommons.org/licenses/by/4.0/'>CC BY 4.0 license</a> allows others to share and adapt the work with proper attribution.",
    )

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
        ]

        widgets = {
            "strengths": forms.Textarea(
                attrs={
                    "placeholder": (
                        "Give a point-by-point "
                        "(numbered 1-, 2-, ...) list of the paper's strengths"
                    ),
                    "rows": 10,
                    "cols": 100,
                }
            ),
            "weaknesses": forms.Textarea(
                attrs={
                    "placeholder": (
                        "Give a point-by-point "
                        "(numbered 1-, 2-, ...) list of the paper's weaknesses"
                    ),
                    "rows": 10,
                    "cols": 100,
                }
            ),
            "report": forms.Textarea(
                attrs={
                    "placeholder": (
                        "Your general remarks. Are this Journal's acceptance criteria met? "
                        "Would you recommend publication in another Journal instead?"
                    ),
                    "rows": 10,
                    "cols": 100,
                }
            ),
            "requested_changes": forms.Textarea(
                attrs={
                    "placeholder": "Give a numbered (1-, 2-, ...) list of specifically requested changes",
                    "cols": 100,
                }
            ),
        }

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
        self.request = kwargs.pop("request", None)

        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False

        # Required fields on submission; optional on save as draft
        self.fields["report"].required = True
        self.fields["recommendation"].required = True
        if "save_draft" in self.data:
            self.fields["report"].required = False
            self.fields["recommendation"].required = False
            self.fields["license_agreement"].required = False

        #! Temporary annotation this field was made public:
        self.fields[
            "recommendation"
        ].help_text = (
            "As of April 2024, report recommendations are also publicly visible."
        )

        if self.submission.eicrecommendations.active().exists():
            # An active EICRecommendation is already formulated. This Report will be flagged.
            self.report_type = REPORT_POST_EDREC

        if contributor := self.request.user.contributor:
            self.fields["anonymity"].choices = [
                ("anonymous", "Publish report anonymously"),
                ("eponymous", f"Publish report as {contributor.profile.full_name}"),
            ]

    def save(self):
        """
        Update meta data if ModelForm is submitted (non-draft).
        Possibly overwrite the default status if user asks for saving as draft.
        """
        report = super().save(commit=False)
        report.report_type = self.report_type

        report.submission = self.submission
        report.date_submitted = timezone.now()

        report.anonymous = self.cleaned_data["anonymity"] != "eponymous"

        # Save with right status asked by user
        if "save_draft" in self.data:
            report.status = STATUS_DRAFT
        elif "save_submit" in self.data:
            report.status = STATUS_UNVETTED

            # Update invitation and report meta data if exist
            invitations = self.submission.referee_invitations.filter(
                referee=report.author.profile
            )
            updated_invitations = invitations.update(fulfilled=True)
            invitations.filter(accepted=None).update(
                accepted=True, date_responded=timezone.now()
            )
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
                attrs={"rows": 15, "placeholder": "Write your message in this box."}
            ),
        }


######################
# EIC Recommendation #
######################


class EICRecommendationForm(forms.ModelForm):
    """Formulate an EICRecommendation."""

    required_css_class = "required-asterisk"

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
                    "rows": 3,
                }
            ),
            "requested_changes": forms.Textarea(
                {
                    "placeholder": (
                        "If you request revisions, give a numbered (1-, 2-, ...)"
                        " list of specifically requested changes"
                    ),
                    "rows": 3,
                }
            ),
            "remarks_for_editorial_college": forms.Textarea(
                {
                    "placeholder": (
                        "If you recommend to accept or reject the manuscript, the Editorial College"
                        " will vote. Summarize the reasons for your recommendation. Focus especially"
                        " on the aspects that do not directly follow from the referee reports."
                    ),
                    "rows": 3,
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

        super().__init__(*args, **kwargs)

        self.layout_fields = {}
        self.layout_fields["for_journal"] = Div(Field("for_journal"))
        self.layout_fields["recommendation"] = Div(Field("recommendation"))
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div(
                    self.layout_fields["for_journal"],
                    Div(
                        Div(
                            self.layout_fields["recommendation"],
                            css_class="col-12 col-lg",
                        ),
                        Div(Field("tier"), css_class="col-12 col-lg-auto"),
                        css_class="row mb-0",
                    ),
                    Field("remarks_for_authors"),
                    Field("requested_changes"),
                    Field("remarks_for_editorial_college"),
                    css_class="col-12",
                ),
                css_class="row",
            )
        )
        self.fields["recommendation"].help_text = (
            "Selecting any of the three Publish choices means that you recommend publication.<br>"
            "Which one you choose simply indicates your ballpark evaluation of the "
            "submission's quality and has no further consequence on the publication."
        )

        self.fields["for_journal"].initial = self.submission.submitted_to
        if self.reformulate:
            latest_recommendation = self.earlier_recommendations.first()
            if latest_recommendation:
                self.fields["for_journal"].initial = latest_recommendation.for_journal
                self.fields[
                    "recommendation"
                ].initial = latest_recommendation.recommendation

        # Determine help points for the journal selection
        alternative_journal_ids = (
            self.submission.submitted_to.alternative_journals.active().values_list(
                "id", flat=True
            )
        )
        for_journal_qs = Journal.objects.filter(
            id__in=list(alternative_journal_ids) + [self.submission.submitted_to.id]
        )
        self.fields["for_journal"].queryset = for_journal_qs
        self.fields["for_journal"].empty_label = "Any/All Journals"

        can_recommend_for_selections = for_journal_qs.filter(
            name__contains="Selections"
        ).exists()
        can_recommend_for_core = for_journal_qs.filter(name__contains="Core").exists()
        journal_help_points = []
        if can_recommend_for_selections:
            journal_help_points.append(
                "SciPost Selections: means article in field flagship journal "
                "(SciPost Physics, Astronomy, Biology, Chemistry...) "
                "with extended abstract published separately in SciPost Selections. "
                "Only choose this for an <em>exceptionally</em> good submission to a flagship journal."
            )
        if can_recommend_for_core:
            journal_help_points.append(
                "A submission to a flagship which does not meet the latter's "
                "tough expectations and criteria can be recommended for publication "
                "in the field's Core journal (if it exists)."
            )
            journal_help_points.append(
                "Conversely, an extremely good submission to a field's Core journal can be "
                "recommended for publication in the field's flagship, provided "
                "it fulfils the latter's expectations and criteria."
            )

        if journal_help_points:
            journal_help_points_HTML = HTML(
                '<div class="bg-info bg-opacity-25 p-2 mb-2">Please be aware of all the points below!'
                + '<ul class="mb-0">'
                + "".join([f"<li>{point}</li>" for point in journal_help_points])
                + "</ul>"
                + "</div>"
            )
            self.layout_fields["for_journal"].append(journal_help_points_HTML)

        # Hide the tier field if the recommendation is not to publish
        recommendation_data = self.data.get("recommendation")
        recommendation_initial = self.fields["recommendation"].initial
        hide_tier = True
        if recommendation_data:
            hide_tier = recommendation_data != str(EIC_REC_PUBLISH)
        elif recommendation_initial:
            hide_tier = recommendation_initial != EIC_REC_PUBLISH

        if hide_tier:
            self.fields["tier"].widget = forms.HiddenInput()
            self.fields["tier"].required = False

        should_mandate_requested_changes = False
        if recommendation_data:
            should_mandate_requested_changes = recommendation_data in [
                str(EIC_REC_MINOR_REVISION),
                str(EIC_REC_MAJOR_REVISION),
            ]
        else:
            should_mandate_requested_changes = recommendation_initial in [
                EIC_REC_MINOR_REVISION,
                EIC_REC_MAJOR_REVISION,
            ]
        if should_mandate_requested_changes:
            self.fields["requested_changes"].required = True
        else:
            self.fields["requested_changes"].required = False

        should_mandate_remarks_for_editorial_college = False
        if recommendation_data:
            should_mandate_remarks_for_editorial_college = recommendation_data in [
                str(EIC_REC_PUBLISH),
                str(EIC_REC_REJECT),
            ]
        elif recommendation_initial:
            should_mandate_remarks_for_editorial_college = recommendation_initial in [
                EIC_REC_PUBLISH,
                EIC_REC_REJECT,
            ]
        if should_mandate_remarks_for_editorial_college:
            self.fields["remarks_for_editorial_college"].required = True
        else:
            self.fields["remarks_for_editorial_college"].required = False

        should_mandate_remarks_for_authors = False
        if recommendation_data:
            should_mandate_remarks_for_authors = recommendation_data == str(
                EIC_REC_REJECT
            )
        elif recommendation_initial:
            should_mandate_remarks_for_authors = (
                recommendation_initial == EIC_REC_REJECT
            )

        if should_mandate_remarks_for_authors:
            self.fields["remarks_for_authors"].required = True
        else:
            self.fields["remarks_for_authors"].required = False

        self.load_assignment()

    def clean(self):
        cleaned_data = super().clean()
        journal = cleaned_data.get("for_journal")
        recommendation = cleaned_data.get("recommendation")

        if recommendation is None:
            self.add_error(
                "recommendation",
                "You must select a recommendation for this manuscript.",
            )

        if recommendation == EIC_REC_PUBLISH:
            if not cleaned_data["tier"]:
                self.add_error(
                    "tier",
                    "If you recommend publication, please also provide a Tier.",
                )
        if (
            recommendation in (EIC_REC_PUBLISH, EIC_REC_REJECT)
            and (remarks_ed_col := cleaned_data.get("remarks_for_editorial_college"))
            and len(remarks_ed_col) < 10
        ):
            self.add_error(
                "remarks_for_editorial_college",
                "You must substantiate your recommendation to accept or reject the manuscript.",
            )
        if journal is None and recommendation != EIC_REC_REJECT:
            self.add_error(
                "for_journal",
                "A specific journal must be chosen for any recommendation other than rejection.",
            )

        if journal and (
            self.submission.nr_unique_thread_vetted_reports
            < journal.minimal_nr_of_reports
        ):
            if recommendation == EIC_REC_PUBLISH:
                self.add_error(
                    "recommendation",
                    "The number of latest vetted reports in this thread"
                    " ({total_reports}) is too low for this journal"
                    " ({min_reports}) to recommend publication.".format(
                        total_reports=self.submission.nr_unique_thread_vetted_reports,
                        min_reports=journal.minimal_nr_of_reports,
                    ),
                )
            elif recommendation in [EIC_REC_MINOR_REVISION, EIC_REC_MAJOR_REVISION]:
                self.layout_fields["recommendation"].append(
                    HTML(
                        '<div class="bg-warning bg-opacity-10 p-2 mb-2">'
                        "<p>At least {min_reports} report(s) from different referees are needed to accept a paper "
                        "in {journal}, whereas you currently have acquired {total_reports} of them. If you request a revision for {journal}, you will need to secure "
                        "the remaining reports in the next refereeing round before recommending acceptance.</p>"
                        '<p class="mb-0">You may continue with this recommendation now and secure the reports later, or <a href="{editorial_page_url}">go back</a> to try obtaining them in this round.</p></div>'.format(
                            journal=journal,
                            total_reports=self.submission.nr_unique_thread_vetted_reports,
                            min_reports=journal.minimal_nr_of_reports,
                            editorial_page_url=reverse(
                                "submissions:editorial_page",
                                kwargs={
                                    "identifier_w_vn_nr": self.submission.preprint.identifier_w_vn_nr
                                },
                            ),
                        ),
                    ),
                )

    def full_clean(self) -> None:
        super_clean = super().full_clean()

        if not self.data.get("submit"):
            self.errors.clear()

        return super_clean

    def is_valid(self) -> bool:
        super_valid = super().is_valid()

        if not self.data.get("submit"):
            return False

        return super_valid

    def save(self):
        # If the cycle hadn't been chosen, set it to the DirectCycle
        if not self.submission.refereeing_cycle:
            self.submission.refereeing_cycle = CYCLE_DIRECT_REC
            self.submission.save()

        recommendation = super().save(commit=False)
        recommendation.formulated_by = self.submission.editor_in_charge
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
                status=Submission.AWAITING_RESUBMISSION,
            )

            if self.assignment:
                # The EIC has fulfilled this editorial assignment.
                self.assignment.status = EditorialAssignment.STATUS_COMPLETED
                self.assignment.save()

            # Add SubmissionEvents for both Author and EIC
            self.submission.add_general_event(
                event_text.format(
                    recommendation.get_for_journal_short_display(),
                    recommendation.get_recommendation_display(),
                )
            )

        elif recommendation.recommendation in [
            EIC_REC_PUBLISH,
            EIC_REC_REJECT,
        ]:
            # if rec is to publish, specify the tiering (deleting old ones first):
            if recommendation.recommendation == EIC_REC_PUBLISH:
                tiering = SubmissionTiering(
                    submission=self.submission,
                    fellow=self.submission.editor_in_charge,
                    for_journal=recommendation.for_journal,
                    tier=self.cleaned_data["tier"],
                )
                tiering.save()

            # set correct status for Submission
            Submission.objects.filter(id=self.submission.id).update(
                open_for_reporting=False,
                open_for_commenting=False,
                reporting_deadline=timezone.now(),
                needs_coauthorships_update=True,  # to prepare for voting
                status=Submission.VOTING_IN_PREPARATION,
            )

            # Add SubmissionEvent for EIC only
            self.submission.add_event_for_eic(
                event_text.format(
                    recommendation.get_for_journal_short_display(),
                    recommendation.get_recommendation_display(),
                )
            )

        else:
            raise exceptions.InvalidRecommendationError(recommendation.recommendation)

        if self.earlier_recommendations:
            self.earlier_recommendations.update(active=False, status=DEPRECATED)

            # All reports already submitted are now formulated *after* eic rec formulation
            Report.objects.filter(
                submission__eicrecommendations__in=self.earlier_recommendations
            ).update(report_type=REPORT_NORMAL)

        recommendation.save()

        # The EIC should vote in favour of their own recommendation
        # This should be done after the recommendation is saved, so that the
        # id is determined for use in the ManyToMany relation.
        # Tiering has already been created above, and no special objects are required
        # in the event of submission rejection.
        recommendation.eligible_to_vote.add(recommendation.formulated_by)
        recommendation.voted_for.add(recommendation.formulated_by)
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

    def __init__(self, *args, **kwargs):
        self.recommendation: "EICRecommendation" = kwargs.pop("recommendation")
        super().__init__(*args, **kwargs)

        alt_journal_ids = list(
            self.recommendation.for_journal.alternative_journals.active().values_list(
                "id", flat=True
            )
        )
        self.fields["alternative_for_journal"].queryset = Journal.objects.filter(
            id__in=[self.recommendation.for_journal.id] + alt_journal_ids
        )

    def clean(self):
        cleaned_data = super().clean()
        vote = cleaned_data.get("vote", None)
        alt_recommendation = int(cleaned_data.get("alternative_recommendation", 0))
        alt_journal = cleaned_data.get("alternative_for_journal", None)

        if vote == "disagree" and (alt_journal is None or alt_recommendation == ""):
            raise forms.ValidationError(
                "If you disagree, you must provide an alternative recommendation "
                "(by filling both the for journal and recommendation fields)."
            )

        is_same_journal = alt_journal == self.recommendation.for_journal
        is_same_recommendation = (
            alt_recommendation == self.recommendation.recommendation
        )
        if is_same_journal and is_same_recommendation:
            raise forms.ValidationError(
                "The alternative recommendation must differ from the original recommendation "
                "in either the Journal or the kind of recommendation."
            )


class RecommendationRemarkForm(forms.Form):
    """Add a remark to an EICRecommendation."""

    remark = forms.CharField(
        widget=forms.Textarea(
            attrs={"rows": 5, "placeholder": "Write your remark in this box."}
        ),
        label="",
    )

    def __init__(self, *args, **kwargs):
        identifier_w_vn_nr = kwargs.pop("identifier_w_vn_nr")
        self.rec_id = kwargs.pop("rec_id")
        self.contributor = kwargs.pop("contributor")
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.attrs = {
            "hx-target": "#recommendation-remarks",
            "hx-post": reverse(
                "submissions:pool:decisionmaking:_hx_recommendation_remarks",
                kwargs={
                    "identifier_w_vn_nr": identifier_w_vn_nr,
                    "rec_id": self.rec_id,
                },
            ),
        }
        self.helper.layout = Layout(
            Field("remark"),
            ButtonHolder(
                Submit("submit", "Add remark", css_class="mt-2 btn btn-primary")
            ),
        )

    def save(self):
        """Save the remark."""
        remark = Remark(
            recommendation=get_object_or_404(EICRecommendation, id=self.rec_id),
            contributor=self.contributor,
            remark=self.cleaned_data["remark"],
        )
        remark.save()
        return remark


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
        if "submission" in self.initial:
            self.fields["submission"].queryset = Submission.objects.filter(
                pk=self.initial["submission"],
            )
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
                status=Submission.REFEREEING_IN_PREPARATION,
                refereeing_cycle=CYCLE_UNDETERMINED,
                acceptance_date=None,
                visible_public=True,
                latest_activity=timezone.now(),
            )
            self.submission.editorial_assignments.filter(
                to=self.submission.editor_in_charge,
                status=EditorialAssignment.STATUS_COMPLETED,
            ).update(status=EditorialAssignment.STATUS_ACCEPTED)
            self.submission.eicrecommendations.active().update(status=DEPRECATED)
            self.submission.editorialdecision_set.update(
                status=EditorialDecision.DEPRECATED
            )

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

    referee_invitation_emails = forms.MultipleChoiceField()

    class Meta:
        model = Submission
        fields = ("refereeing_cycle",)
        widgets = {"refereeing_cycle": forms.RadioSelect}

    def __init__(self, *args, **kwargs):
        """Update choices and queryset."""
        super().__init__(*args, **kwargs)
        self.fields["refereeing_cycle"].choices = SUBMISSION_CYCLE_CHOICES

        all_invitations_in_thread = (
            RefereeInvitation.objects.filter(
                submission__thread_hash=self.instance.thread_hash
            )
            .order_by("referee", "-date_invited")
            .distinct()
        )
        self.fields["referees_reinvite"].queryset = all_invitations_in_thread
        self.fields["referee_invitation_emails"].choices = [
            (email, email)
            for email in all_invitations_in_thread.values_list(
                "referee__emails__email", flat=True
            )
        ]

    def clean(self):
        cleaned_data = super().clean()

        reinvite_referees = cleaned_data.get("referees_reinvite")
        selected_emails = cleaned_data.get("referee_invitation_emails")

        email_to_invitation_map = {
            profile_email.email: invitation
            for invitation in reinvite_referees
            for profile_email in invitation.referee.emails.all()
        }

        # Edit the invitation instances with the selected emails
        edited_invitations = []
        for email in selected_emails:
            if invitation := email_to_invitation_map.get(email):
                invitation.email_address = email
                edited_invitations.append(invitation)

        cleaned_data["referees_reinvite"] = edited_invitations

        return cleaned_data

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
                self.fields["file"] = (
                    forms.FileField()
                )  # Add this field now it's needed
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
                iThenticate_plagiarism_report=report
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
        from ..plagiarism import iThenticate

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


class RefereeIndicationForm(forms.ModelForm):
    class Meta:
        model = RefereeIndication
        exclude = ["submission", "indicated_by"]

    referee = forms.ModelChoiceField(
        queryset=Profile.objects.eponymous(),
        widget=HTMXDynSelWidget(
            url=reverse_lazy("profiles:profile_dynsel"),
        ),
        required=False,
        help_text="Preferably select a referee from the list. If not found, fill in the fields below.",
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2, "maxlength": 255}),
        help_text="Short reason for this indication; <strong>mandatory when advising against</strong>.",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.submission = kwargs.pop("submission")
        self.profile = kwargs.pop("profile")

        if not isinstance(self.profile, Profile):
            raise ValueError("Profile object is required for this form.")

        if not isinstance(self.submission, Submission):
            raise ValueError("Submission object is required for this form.")

        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        # self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        Field("indication"),
                        Field("reason"),
                        css_class="row mb-0",
                    ),
                    css_class="col-12 col-sm-4 col-md-3",
                ),
                Div(
                    Div(
                        Field("referee", css_class="col"),
                        css_class="row mb-0",
                    ),
                    Div(
                        Div(Field("first_name"), css_class="col-12 col-sm-6 col-md"),
                        Div(Field("last_name"), css_class="col-12 col-sm-6 col-md"),
                        Div(Field("affiliation"), css_class="col-12 col-sm-6 col-md"),
                        Div(Field("email_address"), css_class="col-12 col-sm-6 col-md"),
                        css_class="row",
                    ),
                    css_class="col",
                ),
                Div(Field("id", type="hidden"), css_class="d-none"),
                css_class="row",
            )
        )

        # If user is not an author, edadmin, or a college member, hide the "advising against" option
        is_author = self.profile.id in self.submission.authors.values_list(
            "profile__id", flat=True
        )
        is_fellow = self.profile.id in self.submission.fellows.values_list(
            "contributor__profile__id", flat=True
        )
        try:
            is_ed_admin = is_edadmin(self.profile.contributor.user)
        except Contributor.DoesNotExist:
            is_ed_admin = False
        if not (is_author or is_fellow or is_ed_admin):
            self.fields["indication"].choices = [
                RefereeIndication.INDICATION_CHOICES[0]
            ]
            self.fields[
                "reason"
            ].help_text = "Optional short reason for this indication."

        for field in ["first_name", "last_name", "affiliation", "email_address"]:
            self.fields[field].label = "Ref. " + self.fields[field].label.capitalize()

    def clean(self):
        cleaned_data = super().clean()

        referee = cleaned_data.get("referee")
        referee_info_fields = [
            cleaned_data.get("first_name"),
            cleaned_data.get("last_name"),
            cleaned_data.get("email_address"),
        ]

        if referee is None and not all(referee_info_fields):
            self.add_error(
                None,
                "If you don't select a referee, you must provide all the necessary information.",
            )

        if cleaned_data.get("indication") == RefereeIndication.INDICATION_AGAINST:
            reason = cleaned_data.get("reason")
            if reason is None or reason == "":
                self.add_error(
                    "reason",
                    "You must provide a reason when indicating against a referee.",
                )
            elif len(reason) < 10:
                self.add_error(
                    "reason",
                    "The reason is too short, please provide a more detailed explanation.",
                )

        # Check if the referee has already been indicated by the user
        same_indications = RefereeIndication.objects.filter(
            submission=self.submission,
            referee=referee,
            indicated_by=self.profile,
        )
        # If the indication already exists and is being updated, exclude it from the check
        if previous_indication := cleaned_data.get("id"):
            same_indications = same_indications.exclude(id=previous_indication.id)
        if same_indications.exists():
            self.add_error(
                None,
                "You have already indicated this referee for this submission.",
            )

        return cleaned_data

    def save(self, commit=True):
        indication = super().save(commit=False)
        indication.submission = self.submission
        indication.indicated_by = self.profile

        if commit:
            indication.save()
        return indication
