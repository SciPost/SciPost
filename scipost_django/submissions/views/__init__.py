__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
import re

from django.core.paginator import Paginator
from django.template.response import TemplateResponse

from django.contrib import messages
from django.contrib.auth.decorators import (
    user_passes_test,
    login_required,
    permission_required,
)
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction, IntegrityError
from django.db.models import Q, Exists, OuterRef, QuerySet
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, get_list_or_404, render, redirect
from django.template import Template, Context
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.html import format_html
from django.utils.timezone import timedelta
from django.views.generic.base import RedirectView
from django.views.generic.detail import SingleObjectMixin, DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from dal import autocomplete
import sentry_sdk

from common.views import HXFormSetView, empty
from profiles.utils import resolve_profile

from scipost.permissions import (
    HTMXPermissionsDenied,
    HTMXResponse,
    permission_required_htmx,
)
from submissions.models.assignment import ConditionalAssignmentOffer
from submissions.models.communication import EditorialCommunication

from ..constants import (
    ED_COMM_CHOICES,
    STATUS_VETTED,
    STATUS_DRAFT,
    CYCLE_DIRECT_REC,
    EIC_REC_PUBLISH,
    EIC_REC_REJECT,
    DECISION_FIXED,
    FIGSHARE_PREPRINT_SERVERS,
)
from ..helpers import check_verified_author, check_unverified_author
from ..models import (
    Submission,
    PreprintServer,
    EICRecommendation,
    SubmissionTiering,
    AlternativeRecommendation,
    EditorialDecision,
    EditorialAssignment,
    RefereeInvitation,
    Report,
    SubmissionEvent,
    RefereeIndication,
)
from ..mixins import SubmissionMixin, SubmissionAdminViewMixin
from ..forms import (
    InviteRefereeSearchFrom,
    RefereeIndicationForm,
    ReportIntendedDeliveryForm,
    SciPostPrefillForm,
    ArXivPrefillForm,
    ChemRxivPrefillForm,
    FigsharePrefillForm,
    OSFPreprintsPrefillForm,
    ConfigureRefereeInvitationForm,
    SubmissionCollectionsForm,
    SubmissionForm,
    SubmissionPoolSearchForm,
    SubmissionOldSearchForm,
    RecommendationVoteForm,
    EditorialAssignmentForm,
    VetReportForm,
    SetRefereeingDeadlineForm,
    iThenticateReportForm,
    VotingEligibilityForm,
    WithdrawSubmissionForm,
    ConsiderRefereeInvitationForm,
    EditorialCommunicationForm,
    ReportForm,
    RestartRefereeingForm,
    SubmissionCycleChoiceForm,
    ReportPDFForm,
    SubmissionReportsForm,
    EICRecommendationForm,
    EditorialDecisionForm,
    SubmissionTargetJournalForm,
    SubmissionTargetProceedingsForm,
    SubmissionPreprintFileForm,
    SubmissionPreassignmentForm,
    PreassignEditorsFormSet,
    SubmissionReassignmentForm,
)
from ..utils import SubmissionUtils

from colleges.models import PotentialFellowship, Fellowship
from colleges.permissions import (
    fellowship_required,
    fellowship_or_admin_required,
    is_edadmin,
    is_edadmin_or_senior_fellow,
)
from comments.forms import CommentForm
from common.helpers import get_new_secrets_key
from common.utils import get_current_domain, workdays_between
from invitations.constants import STATUS_SENT
from invitations.models import RegistrationInvitation
from journals.models import Journal, Publication
from mails.utils import DirectMailUtil
from mails.views import MailEditorSubview
from ontology.models import Topic
from ontology.forms import SpecialtyInlineForm, TopicDynSelForm
from preprints.models import Preprint
from production.forms import ProofsDecisionForm
from production.utils import get_or_create_production_stream
from profiles.models import Profile, ProfileEmail
from profiles.forms import AddProfileEmailForm, SimpleProfileForm
from scipost.constants import TITLE_DR, INVITATION_REFEREEING
from scipost.decorators import is_contributor_user
from scipost.forms import RemarkForm, SearchTextForm
from scipost.mixins import PaginationMixin, PermissionsMixin
from scipost.models import Contributor, Remark
from scipost.views import prompt_to_login

################
# Autocomplete #
################


class SubmissionAutocompleteView(autocomplete.Select2QuerySetView):
    """
    View to feed the Select2 widget.
    """

    def get_queryset(self):
        qs = Submission.objects.public_listed()
        if self.q:
            qs = qs.filter(
                Q(preprint__identifier_w_vn_nr__icontains=self.q)
                | Q(title__icontains=self.q)
                | Q(author_list__icontains=self.q)
            )
        return qs.order_by("-submission_date").prefetch_related("publication")

    def get_result_label(self, item):
        """
        Give same info as in ``Submission.__str__()`` but with carriage returns.
        """
        end_info = ""
        if item.is_latest:
            end_info = " (latest version)"
        else:
            end_info = " (deprecated version " + str(item.thread_sequence_order) + ")"
        if hasattr(item, "publication") and item.publication.is_published:
            end_info += " (published as %s (%s))" % (
                item.publication.doi_string,
                item.publication.publication_date.strftime("%Y"),
            )
        return format_html(
            '<strong>{}</strong><br>{}<br><span class="text-muted">by {}</span><br>{}',
            item.preprint.identifier_w_vn_nr,
            item.title,
            item.author_list,
            end_info,
        )


###################
#
# Submission views
#
###################


@login_required
@permission_required("scipost.can_submit_manuscript", raise_exception=True)
def submit_manuscript(request):
    """
    Initiate submission by choosing either resubmission or new submission process.
    """
    # For each integrated preprint server, redirect to appropriate view
    context = {
        "journals": Journal.objects.submission_allowed(),
        "resubmission_candidates": Submission.objects.candidate_for_resubmission(
            request.user
        ),
    }
    return render(request, "submissions/submit_manuscript.html", context)


@login_required
@permission_required("scipost.can_submit_manuscript", raise_exception=True)
def submit_choose_journal(request, acad_field=None):
    """
    Choose a Journal. If `thread_hash` is given as GET parameter, this is a resubmission.
    """
    journals = Journal.objects.submission_allowed()
    if acad_field:
        journals = journals.filter(college__acad_field=acad_field)
    context = {
        "acad_field": acad_field,
        "journals": journals,
    }
    if request.GET.get("thread_hash"):
        context["thread_hash"] = request.GET.get("thread_hash")
    return render(request, "submissions/submit_choose_journal.html", context)


@login_required
@permission_required("scipost.can_submit_manuscript", raise_exception=True)
def submit_choose_preprint_server(request, journal_doi_label):
    """
    Choose a preprint server. If `thread_hash` is given as a GET parameter, this is a resubmission.
    """
    journal = get_object_or_404(Journal, doi_label=journal_doi_label)
    # Guard against inactive journals
    if not (journal.active or request.user.is_staff):
        raise PermissionDenied("Journal is not active")

    preprint_servers = PreprintServer.objects.filter(
        acad_fields=journal.college.acad_field
    )
    thread_hash = request.GET.get("thread_hash") or None

    # Each integrated preprint server has a prefill form:
    preprint_server_list = []

    # arXiv the beloved, always first (if available in this field)
    if preprint_servers.filter(name="arXiv").exists():
        preprint_server_list.append(
            {
                "server": preprint_servers.get(name="arXiv"),
                "prefill_form": ArXivPrefillForm(
                    requested_by=request.user,
                    journal_doi_label=journal_doi_label,
                    thread_hash=thread_hash,
                ),
            }
        )

    # ChemRxiv
    if preprint_servers.filter(name="ChemRxiv").exists():
        preprint_server_list.append(
            {
                "server": preprint_servers.get(name="ChemRxiv"),
                "prefill_form": ChemRxivPrefillForm(
                    requested_by=request.user,
                    journal_doi_label=journal_doi_label,
                    thread_hash=thread_hash,
                ),
            }
        )

    # then all OSF-based preprint servers
    for ps in preprint_servers.filter(served_by__name="OSFPreprints"):
        preprint_server_list.append(
            {
                "server": ps,
                "prefill_form": OSFPreprintsPrefillForm(
                    initial={"osfpreprints_preprint_server": ps},
                    requested_by=request.user,
                    journal_doi_label=journal_doi_label,
                    thread_hash=thread_hash,
                ),
            }
        )

    # then all Figshare-based preprint servers
    for ps in preprint_servers.filter(served_by__name="Figshare"):
        preprint_server_list.append(
            {
                "server": ps,
                "prefill_form": FigsharePrefillForm(
                    initial={"figshare_preprint_server": ps},
                    requested_by=request.user,
                    journal_doi_label=journal_doi_label,
                    thread_hash=thread_hash,
                ),
            }
        )

    # We put the SciPost server last, since we prefer authors to use external servers
    preprint_server_list.append(
        {
            "server": preprint_servers.get(name="SciPost"),
            "prefill_form": SciPostPrefillForm(
                requested_by=request.user,
                journal_doi_label=journal_doi_label,
                thread_hash=thread_hash,
            ),
        }
    )

    context = {
        "journal": journal,
        "thread_hash": thread_hash,
        "preprint_server_list": preprint_server_list,
    }
    return render(request, "submissions/submit_choose_preprint_server.html", context)


class RequestSubmissionView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Formview to submit a new manuscript (Submission)."""

    permission_required = "scipost.can_submit_manuscript"
    form_class = SubmissionForm
    template_name = "submissions/submission_form.html"

    def __init__(self, **kwargs):
        self.prefill_form = None
        self.initial_data = {}
        super().__init__(**kwargs)

    def get(self, request, journal_doi_label):
        """
        Redirect to `submit_choose_preprint_server` if preprint identifier is not known.
        """
        # Guard against inactive journals
        journal = get_object_or_404(Journal, doi_label=journal_doi_label)
        if not (journal.active or request.user.is_staff):
            raise PermissionDenied("Journal is not active")

        if self.prefill_form.is_valid():
            if self.prefill_form.is_resubmission():
                resubmessage = (
                    "An earlier preprint was found within this submission thread."
                    "\nYour Submission will thus be handled as a resubmission."
                    "\nWe have pre-filled the form where possible. "
                    "Please check everything carefully!"
                )
                messages.success(request, resubmessage, fail_silently=True)
            else:
                readymessage = (
                    "Your submission form is now ready to be filled in. "
                    "\nPlease check everything carefully!"
                )
                messages.success(request, readymessage, fail_silently=True)
            # Gather data from preprint server API if prefill form is valid
            self.initial_data = self.prefill_form.get_prefill_data()
            return super().get(request)
        else:
            for code, err in self.prefill_form.errors.items():
                messages.warning(request, err[0])
            kwargs = {"journal_doi_label": journal_doi_label}
            redirect_url = reverse(
                "submissions:submit_choose_preprint_server", kwargs=kwargs
            )
            if request.GET.get("thread_hash"):
                redirect_url += "?thread_hash=%s" % request.GET.get("thread_hash")
            return redirect(redirect_url)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["journal"] = get_object_or_404(
            Journal, doi_label=self.kwargs.get("journal_doi_label")
        )
        context["thread_hash"] = self.request.GET.get("thread_hash")
        return context

    def get_form_kwargs(self):
        """Form requires extra kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs["requested_by"] = self.request.user
        kwargs["submitted_to_journal"] = get_object_or_404(
            Journal, doi_label=self.kwargs.get("journal_doi_label")
        )
        kwargs["initial"] = getattr(self, "initial_data", {})
        return kwargs

    # @transaction.atomic
    def form_valid(self, form):
        """Redirect and send out mails if all data is valid."""
        submission = form.save()
        self.submission = submission

        submission.add_general_event("Submitted to %s." % str(submission.submitted_to))

        text = (
            "<h3>Thank you for your Submission to SciPost</h3>"
            "Your Submission will soon be handled by an Editor."
        )
        messages.success(self.request, text)

        if form.is_resubmission():
            # Send emails
            mail_util = DirectMailUtil(
                "eic/submission_reappointment", submission=submission
            )
            mail_util.send_mail()
            mail_util = DirectMailUtil(
                "authors/acknowledge_resubmission", submission=submission
            )
            mail_util.send_mail()
        else:
            # Send emails
            mail_util = DirectMailUtil(
                "authors/acknowledge_submission", submission=submission
            )
            mail_util.send_mail()

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        """Add warnings as messages to make those more explicit."""
        for error_messages in form.errors.values():
            messages.warning(self.request, *error_messages)
        return super().form_invalid(form)

    def get_success_url(self):
        """Redirect to the indicate referees step."""

        url_kwargs = {"identifier_w_vn_nr": self.submission.preprint.identifier_w_vn_nr}
        if not self.submission.is_resubmission:
            # First submission, redirect to indicate referees
            return reverse("submissions:submit_indicate_referees", kwargs=url_kwargs)
        else:
            return reverse("submissions:submission", kwargs=url_kwargs)


class RequestSubmissionUsingSciPostView(RequestSubmissionView):
    """Formview to submit a new Submission using SciPost's preprint server."""

    def get(self, request, journal_doi_label):
        self.prefill_form = SciPostPrefillForm(
            requested_by=self.request.user,
            journal_doi_label=journal_doi_label,
            thread_hash=request.GET.get("thread_hash"),
        )
        return super().get(request, journal_doi_label)


class RequestSubmissionUsingArXivView(RequestSubmissionView):
    """Formview to submit a new Submission using arXiv."""

    def get(self, request, journal_doi_label):
        """
        Redirect to `submit_choose_preprint_server` if arXiv identifier is not known.
        """
        self.prefill_form = ArXivPrefillForm(
            request.GET or None,
            requested_by=self.request.user,
            journal_doi_label=journal_doi_label,
            thread_hash=request.GET.get("thread_hash"),
        )
        return super().get(request, journal_doi_label)


class RequestSubmissionUsingChemRxivView(RequestSubmissionView):
    """Formview to submit a new Submission using ChemRxiv."""

    def get(self, request, journal_doi_label):
        """
        Redirect to `submit_choose_preprint_server` if ChemRxiv identifier is not known.
        """
        self.prefill_form = ChemRxivPrefillForm(
            request.GET or None,
            requested_by=self.request.user,
            journal_doi_label=journal_doi_label,
            thread_hash=request.GET.get("thread_hash"),
        )
        return super().get(request, journal_doi_label)


class RequestSubmissionUsingFigshareView(RequestSubmissionView):
    """Formview to submit a new Submission using Figshare-related servers."""

    def get(self, request, journal_doi_label):
        self.prefill_form = FigsharePrefillForm(
            request.GET or None,
            requested_by=self.request.user,
            journal_doi_label=journal_doi_label,
            thread_hash=request.GET.get("thread_hash"),
        )
        return super().get(request, journal_doi_label)


class RequestSubmissionUsingOSFPreprintsView(RequestSubmissionView):
    """Formview to submit a new Submission using OSFPreprints-related servers."""

    def get(self, request, journal_doi_label):
        self.prefill_form = OSFPreprintsPrefillForm(
            request.GET or None,
            requested_by=self.request.user,
            journal_doi_label=journal_doi_label,
            thread_hash=request.GET.get("thread_hash"),
        )
        return super().get(request, journal_doi_label)


@login_required
@permission_required("scipost.can_submit_manuscript", raise_exception=True)
def submit_indicate_referees(request, identifier_w_vn_nr):
    """
    Inform users of SciPost's unique refereeing process and ask them to indicate referees.

    This page should only be accessible to the submitting author and only before the submission has passed preassignment.
    Afterwards, visitors should be redirected to the main `indicate_referees` page.
    """

    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )

    if (request.user.contributor != submission.submitted_by) and not is_edadmin(
        request.user
    ):
        raise PermissionDenied("You are not the submitting author of this Submission.")

    # Redirect to main referee indications view if passed preassignment of is resubmission
    if submission.status != Submission.INCOMING or submission.is_resubmission:
        return redirect(
            reverse(
                "submissions:referee_indications",
                kwargs={"identifier_w_vn_nr": identifier_w_vn_nr},
            )
        )

    context = {
        "submission": submission,
    }

    return render(request, "submissions/submit_indicate_referees.html", context)


@login_required
def withdraw_manuscript(request, identifier_w_vn_nr):
    """
    Withdrawal of the submission by one of the submitting authors.

    This method performs the following actions:

    * makes the Submission and its previous versions publicly invisible
    * marks any Editorial Assignment as completed
    * deprecates any Editorial Recommendation
    * emailing authors, EIC (cc to EdAdmin)
    * deprecates all outstanding refereeing requests (emailing referees)
    * if an outstanding puboffer exists, mark it as turned down in EdDecision
    * deletes production stream (if started, in case puboffer made)
    * adds an event.

    GET shows the info/confirm page
    POST performs the action and returns to the personal page.
    """
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )

    if request.user.contributor.id != submission.submitted_by.id:
        errormessage = (
            "You are not marked as the submitting author of this Submission, "
            "and thus are not allowed to withdraw it."
        )
        return render(request, "scipost/error.html", {"errormessage": errormessage})

    form = WithdrawSubmissionForm(request.POST or None, submission=submission)
    # form = ConfirmationForm(request.POST or None)
    if form.is_valid():
        if form.is_confirmed():
            submission = form.save()

            # Inform EIC
            if submission.editor_in_charge:
                mail_sender_eic = DirectMailUtil(
                    "eic/inform_eic_manuscript_withdrawn", submission=submission
                )
                mail_sender_eic.send_mail()

            # Confirm withdrawal to authors
            mail_sender_authors = DirectMailUtil(
                "authors/inform_authors_manuscript_withdrawn", submission=submission
            )
            mail_sender_authors.send_mail()

            # Email all referees (if outstanding), cancel all outstanding
            for invitation in submission.referee_invitations.outstanding():
                mail_util = DirectMailUtil(
                    "referees/inform_referee_manuscript_withdrawn",
                    invitation=invitation,
                )
                mail_util.send_mail()
            submission.referee_invitations.outstanding().update(cancelled=True)

            # All done.
            submission.add_general_event(
                "The manuscript has been withdrawn by the authors."
            )
            messages.success(request, "Your manuscript has been withdrawn.")
        else:
            messages.error(request, "Withdrawal procedure aborted")
        return redirect(reverse("scipost:personal_page"))
    context = {"submission": submission, "form": form}
    return render(request, "submissions/withdraw_manuscript.html", context)


@login_required
def extend_assignment_deadline(
    request, identifier_w_vn_nr: str, days: int | None = None
):
    """
    Extend the assignment deadline date of a Submission.

    Accessible to EdAdmin (always) or authors of the Submission (for first extension).
    """
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )

    if submission.assignment_deadline is None:
        raise PermissionDenied("This Submission has no assignment deadline.")

    is_submission_author = request.user.contributor in submission.authors.all()
    if not (is_edadmin(request.user) or is_submission_author):
        raise PermissionDenied("You are not allowed to extend the assignment deadline.")

    # Compute the new assignment deadline if days is given, otherwise use the default
    # For authors, ignore the days even if given
    extension_date = (
        submission.assignment_deadline + timedelta(days=days)
        if days is not None and is_edadmin(request.user)
        else submission.assignment_deadline
        + (submission.submitted_to.assignment_period // 2)
    )

    if extension_date < submission.assignment_deadline:
        raise PermissionDenied("You cannot set an earlier date.")

    if is_submission_author and submission.has_extended_assignment_deadline:
        raise PermissionDenied(
            "You are not allowed to extend the assignment deadline again."
        )

    submission.assignment_deadline = extension_date
    submission.save()

    submission.add_general_event(
        f"The assignment deadline has been extended to {extension_date}."
    )
    messages.success(request, "The assignment deadline has been extended.")

    return redirect(
        reverse(
            "submissions:submission",
            kwargs={"identifier_w_vn_nr": identifier_w_vn_nr},
        )
    )


@login_required
def accept_conditional_assignment_offer(request, identifier_w_vn_nr, offer_id):
    """
    Accept a conditional assignment offer and redirect to the Submission's detail page.

    The offer_id is used to determine the TYPE of offer to accept.
    The accepted offer may actually be different in order to balance the load of the referees.
    """
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    offer = get_object_or_404(
        ConditionalAssignmentOffer,
        id=offer_id,
        submission=submission,
    )

    # Guard against unauthorized access
    if request.user.contributor not in submission.authors.all():
        raise PermissionDenied("Only verified authors can accept conditional offers.")

    # Find all identical offers and sort them by the fellow's ongoing assignments
    # Select the offer with the least ongoing assignments, or the oldest if equal
    if identical_offers := ConditionalAssignmentOffer.objects.filter(
        submission=submission,
        condition_type=offer.condition_type,
        condition_details=offer.condition_details,
        status=ConditionalAssignmentOffer.STATUS_OFFERED,
    ).order_by("offered_on"):
        sorted_offers = sorted(
            identical_offers,
            key=lambda x: x.offered_by.editorial_assignments.ongoing().count(),
        )
        offer = sorted_offers[0]

    try:
        offer.accept(by=request.user.contributor)
        offer.finalize()

        messages.success(request, "The conditional assignment offer has been accepted.")

        # Send email to EIC and authors
        mail_sender_eic = DirectMailUtil(
            "eic/inform_conditional_assignment_offer_accepted",
            offer=offer,
        )
        mail_sender_eic.send_mail()

    except Exception as e:
        raise PermissionDenied(e)

    return redirect(
        reverse(
            "submissions:submission",
            kwargs={"identifier_w_vn_nr": identifier_w_vn_nr},
        )
    )


# Marked for deprecation
class SubmissionListView(PaginationMixin, ListView):
    """List all publicly available Submissions."""

    model = Submission
    form = SubmissionOldSearchForm
    submission_search_list = []
    paginate_by = 10

    def get_queryset(self):
        """Return queryset, filtered with GET request data if given."""
        queryset = Submission.objects.public_latest()
        self.form = self.form(self.request.GET)
        if "field" in self.request.GET:
            queryset = queryset.filter(acad_field__slug=self.request.GET["field"])
        if "specialty" in self.request.GET:
            queryset = queryset.filter(specialties__slug=self.request.GET["specialty"])
        if "to_journal" in self.request.GET:
            queryset = queryset.filter(
                submitted_to__doi_label=self.request.GET["to_journal"]
            )
        elif self.form.is_valid() and self.form.has_changed():
            queryset = self.form.search_results()

        return queryset.order_by("-submission_date")

    def get_context_data(self, **kwargs):
        """Save data related to GET request if found."""
        context = super().get_context_data(**kwargs)

        # Form into the context!
        context["form"] = self.form

        # To customize display in the template
        if "to_journal" in self.request.GET:
            try:
                context["to_journal"] = (
                    Journal.objects.filter(name=self.request.GET["to_journal"])
                    .first()
                    .get_name_display()
                )
            except (Journal.DoesNotExist, AttributeError):
                context["to_journal"] = self.request.GET["to_journal"]
        return context


def submission_detail_wo_vn_nr(request, identifier_wo_vn_nr):
    """Redirect to the latest Submission's detail page."""
    submissions = get_list_or_404(
        Submission, preprint__identifier_w_vn_nr__startswith=identifier_wo_vn_nr
    )
    latest = submissions[0].get_latest_public_version()
    if not latest:
        raise Http404
    return redirect(
        reverse(
            "submissions:submission",
            kwargs={"identifier_w_vn_nr": latest.preprint.identifier_w_vn_nr},
        )
    )


def submission_detail(request, identifier_w_vn_nr):
    """Public detail page of Submission."""

    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    context = {
        "can_read_editorial_information": False,
    }

    # Check if Contributor is author of the Submission
    is_submitting_author = request.user == submission.submitted_by.user
    is_author = check_verified_author(submission, request.user)
    is_author_unchecked = check_unverified_author(submission, request.user)
    is_submission_fellow = submission.fellows.filter(
        contributor__dbuser=request.user.id
    ).exists()

    if not submission.visible_public and not is_author:
        if not request.user.is_authenticated:
            return prompt_to_login(request)

        elif (
            not request.user.has_perm("scipost.can_assign_submissions")
            and not submission.fellows.filter(contributor__dbuser=request.user).exists()
        ):
            raise PermissionDenied()

    if is_author:
        context["proofs_decision_form"] = ProofsDecisionForm()

    if submission.open_for_commenting and request.user.has_perm(
        "scipost.can_submit_comments"
    ):
        context["comment_form"] = CommentForm()

    invited_reports = submission.reports.accepted().invited()
    contributed_reports = submission.reports.accepted().contributed()
    comments = (
        submission.comments.vetted().regular_comments().order_by("-date_submitted")
    )
    author_replies = (
        submission.comments.vetted().author_replies().order_by("-date_submitted")
    )

    # User is referee for the Submission
    if request.user.is_authenticated:
        context["unfinished_report_for_user"] = (
            submission.reports.in_draft().filter(author__dbuser=request.user).first()
        )
        context["invitations"] = submission.referee_invitations.non_cancelled().filter(
            referee=request.user.contributor.profile
        )

        if is_author or is_author_unchecked:
            # Authors are not allowed to read all editorial info! Whatever
            # their permission level is.
            context["can_read_editorial_information"] = False
        else:
            # User may read eg. Editorial Recommendations if they are in the Fellowship
            # and they have no competing interests against the authors of the Submission.
            context["can_read_editorial_information"] = (
                submission.fellows.without_competing_interests_against_submission_authors_of(
                    submission
                )
                .filter(contributor__dbuser=request.user)
                .exists()
            )

            # User may also read eg. Editorial Recommendations if they are editorial administrator.
            if not context["can_read_editorial_information"]:
                context["can_read_editorial_information"] = request.user.has_perm(
                    "can_oversee_refereeing"
                )

    if "invitations" in context and context["invitations"]:
        context["communication"] = (
            submission.editorial_communications.for_referees().filter(
                referee__contributor__dbuser=request.user
            )
        )

    recommendations = submission.eicrecommendations.active()

    has_appraised_submission = (
        submission.qualification_set.filter(
            fellow__contributor__dbuser=request.user.id
        ).exists()
        and submission.readiness_set.filter(
            fellow__contributor__dbuser=request.user.id
        ).exists()
    )

    context.update(
        {
            "submission": submission,
            "recommendations": recommendations,
            "comments": comments,
            "invited_reports": invited_reports,
            "contributed_reports": contributed_reports,
            "author_replies": author_replies,
            "is_submitting_author": is_submitting_author,
            "is_author": is_author,
            "is_author_unchecked": is_author_unchecked,
            "is_submission_fellow": is_submission_fellow,
            "has_appraised_submission": has_appraised_submission,
            "unverified_claims_exist": submission.authorshipclaim_set.filter(status=0).exists(),
        }
    )
    return render(request, "submissions/submission_detail.html", context)


@login_required()
@user_passes_test(is_edadmin)
def _hx_submission_autoupdate_fellowship(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )

    if request.method == "POST":
        submission.auto_updated_fellowship = not submission.auto_updated_fellowship
        submission.save()

    return TemplateResponse(
        request,
        "submissions/_hx_submission_autoupdate_fellowship.html",
        context={"submission": submission},
    )


def _hx_submission_topics(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    context = {
        "submission": submission,
    }
    if request.GET.get("include_matches", None):
        context["matching_topics"] = submission.topics.filter(
            slug__in=[t.slug for t in request.user.contributor.profile.topics.all()],
        )
    if request.user.has_perm("scipost.can_manage_ontology"):
        form = TopicDynSelForm(
            initial={
                "action_url_name": "submissions:_hx_submission_topic_action",
                "action_url_base_kwargs": {
                    "identifier_w_vn_nr": identifier_w_vn_nr,
                    "action": "add",
                },
                "action_target_element_id": f"submission-{submission.pk}-topics",
            }
        )
        context["topic_search_form"] = form
    return render(request, "submissions/_hx_submission_topics.html", context)


@login_required
@permission_required("scipost.can_manage_ontology")
def _hx_submission_topic_action(request, identifier_w_vn_nr, topic_slug, action):
    """
    Add or remove a predefined Topic to an existing Submission object.
    This also adds the Topic to all Submissions predating this one,
    and to any existing associated Publication object.
    """
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    topic = get_object_or_404(Topic, slug=topic_slug)
    if action == "add":
        submission.topics.add(topic)
        for sub in submission.get_other_versions():
            sub.topics.add(topic)
        for publication in submission.publications.all():
            publication.topics.add(topic)
    if action == "remove":
        submission.topics.remove(topic)
        for sub in submission.get_other_versions():
            sub.topics.remove(topic)
        for publication in submission.publications.all():
            publication.topics.remove(topic)
    return redirect(
        reverse(
            "submissions:_hx_submission_topics",
            kwargs={
                "identifier_w_vn_nr": identifier_w_vn_nr,
            },
        )
        + "?include_matches=1",
    )


def _hx_submission_workflow_diagram(request, identifier_w_vn_nr=None):
    """Mermaid workflow diagram of Submission."""
    context = {}
    if identifier_w_vn_nr:
        submission = get_object_or_404(
            Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
        )
        context["submission"] = submission
    return render(request, "submissions/_hx_submission_workflow_diagram.html", context)


def report_attachment(request, identifier_w_vn_nr, report_nr):
    """Download the attachment of a Report if available."""
    report = get_object_or_404(
        Report,
        submission__preprint__identifier_w_vn_nr=identifier_w_vn_nr,
        file_attachment__isnull=False,
        report_nr=report_nr,
    )
    if not report.is_vetted:
        # Only Admins and EICs are allowed to see non-vetted Report attachments.
        if (
            not Submission.objects.in_pool_filter_for_eic(request.user)
            .filter(preprint__identifier_w_vn_nr=identifier_w_vn_nr)
            .exists()
        ):
            raise Http404
    response = HttpResponse(
        report.file_attachment.read(), content_type="application/pdf"
    )
    filename = "{}_report_attachment-{}.pdf".format(
        report.submission.preprint.identifier_w_vn_nr, report.report_nr
    )
    response["Content-Disposition"] = "filename=" + filename
    return response


def report_detail_pdf(request, identifier_w_vn_nr, report_nr):
    """Download the PDF of a Report if available."""
    report = get_object_or_404(
        Report.objects.accepted(),
        submission__preprint__identifier_w_vn_nr=identifier_w_vn_nr,
        pdf_report__isnull=False,
        report_nr=report_nr,
    )
    response = HttpResponse(report.pdf_report.read(), content_type="application/pdf")
    filename = "%s_report-%i.pdf" % (
        report.submission.preprint.identifier_w_vn_nr,
        report.report_nr,
    )
    response["Content-Disposition"] = "filename=" + filename
    return response


def submission_refereeing_package_pdf(request, identifier_w_vn_nr):
    """Down the refereeing package PDF.

    This view let's the user download all Report PDF's in a single merged PDF.
    The merging takes places every time its downloaded to make sure all available report PDF's
    are included and the EdColAdmin doesn't have to compile the package every time again.
    """
    submission = get_object_or_404(
        Submission.objects.public().exclude(pdf_refereeing_pack=""),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    response = HttpResponse(
        submission.pdf_refereeing_pack.read(), content_type="application/pdf"
    )
    filename = "%s-refereeing-package.pdf" % submission.preprint.identifier_w_vn_nr
    response["Content-Disposition"] = "filename=" + filename
    return response


@permission_required("scipost.can_manage_reports", raise_exception=True)
def reports_accepted_list(request):
    """List all accepted Reports.

    This gives an overview of Report that need a PDF update/compilation.
    """
    reports = (
        Report.objects.accepted()
        .order_by("pdf_report", "submission")
        .prefetch_related("submission")
    )

    if request.GET.get("submission"):
        reports = reports.filter(
            submission__preprint__identifier_w_vn_nr=request.GET["submission"]
        )
    context = {"reports": reports}
    return render(request, "submissions/admin/report_list.html", context)


@permission_required("scipost.can_manage_reports", raise_exception=True)
def report_pdf_compile(request, report_id):
    """Form view to receive a auto-generated LaTeX code and submit a pdf version of the Report."""
    report = get_object_or_404(Report.objects.accepted(), id=report_id)
    form = ReportPDFForm(request.POST or None, request.FILES or None, instance=report)
    if form.is_valid():
        report = form.save()
        messages.success(request, "Upload complete.")
        return redirect(reverse("submissions:reports_accepted_list"))
    context = {
        "domain": get_current_domain(),
        "report": report,
        "form": form,
    }
    return render(request, "submissions/admin/report_compile_form.html", context)


@login_required
def _hx_anonymize_report(request: HttpRequest, report_id):
    report = get_object_or_404(Report, id=report_id)

    is_report_author = report.author.user == request.user
    if not (is_edadmin(request.user) or is_report_author):
        raise PermissionDenied

    if is_report_author and report.date_submitted < (
        timezone.now() - datetime.timedelta(days=1)
    ):
        messages.error(
            request,
            "You can only anonymize your own report within 24 hours of submission.",
        )
    else:
        report.anonymous = True
        report.save()
        report.submission.add_event_for_eic(
            f"{request.user.get_full_name()} anonymized "
            f"referee report #{report.report_nr} "
            f"(by {report.author.profile.full_name})"
        )

    return render(
        request,
        "submissions/_report_public.html",
        {"report": report, "submission": report.submission},
    )


@permission_required("scipost.can_manage_reports", raise_exception=True)
def treated_submissions_list(request):
    """List all treated Submissions.

    This gives an overview of Submissions that need a PDF update/compilation of their Reports.
    """
    submissions = (
        Submission.objects.treated()
        .public()
        .order_by("pdf_refereeing_pack", "-acceptance_date")
    )
    context = {"submissions": submissions}
    return render(request, "submissions/treated_submission_list.html", context)


@permission_required("scipost.can_manage_reports", raise_exception=True)
def treated_submission_pdf_compile(request, identifier_w_vn_nr):
    """Form view to receive a auto-generated LaTeX code and submit a pdf version of the Reports."""
    submission = get_object_or_404(
        Submission.objects.treated(), preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    form = SubmissionReportsForm(
        request.POST or None, request.FILES or None, instance=submission
    )
    if form.is_valid():
        form.save()
        messages.success(request, "Upload complete.")
        return redirect(reverse("submissions:treated_submissions_list"))
    context = {
        "domain": get_current_domain(),
        "submission": submission,
        "form": form,
    }
    return render(request, "submissions/treated_submission_pdf_compile.html", context)


######################
# Editorial workflow #
######################


def editorial_workflow(request):
    """Information page for Editorial Fellows.

    Summary page for Editorial Fellows, containing a digest
    of the actions to take to handle Submissions.
    """
    return render(request, "submissions/editorial_workflow.html")


@login_required
@permission_required("scipost.can_assign_submissions", raise_exception=True)
@transaction.atomic
def assignment_failed(request, identifier_w_vn_nr):
    """Reject a Submission in assignment.

    No Editorial Fellow has accepted or volunteered to become Editor-in-charge., hence the
    Submission is rejected. An Editorial Administrator can access this view from the Pool.
    """
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user).seeking_assignment(),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )

    mail_editor_view = MailEditorSubview(
        request,
        mail_code="authors/submissions_assignment_failed",
        instance=submission,
        header_template="submissions/admin/editorial_assignment_failed.html",
    )
    if mail_editor_view.is_valid():
        # Deprecate old Editorial Assignments
        EditorialAssignment.objects.filter(submission=submission).invited().update(
            status=EditorialAssignment.STATUS_DEPRECATED,
        )

        # Update status of Submission
        submission.touch()
        Submission.objects.filter(id=submission.id).update(
            status=Submission.ASSIGNMENT_FAILED,
            visible_pool=False,
            visible_public=False,
        )

        messages.success(
            request,
            "Submission {identifier} has failed assignment and been rejected.".format(
                identifier=submission.preprint.identifier_w_vn_nr
            ),
        )
        messages.success(request, "Authors have been informed by email.")
        mail_editor_view.send_mail()
        return redirect(reverse("submissions:pool:pool"))
    return mail_editor_view.interrupt()


@login_required
@fellowship_required()
def assignments(request):
    """List editorial tasks for a Fellow.

    This page provides a Fellow with an explicit task list
    of editorial actions which should be undertaken.
    """
    assignments = EditorialAssignment.objects.filter(
        to=request.user.contributor
    ).order_by("-date_created")
    assignments_to_consider = assignments.invited()
    current_assignments = assignments.ongoing()

    context = {
        "assignments_to_consider": assignments_to_consider,
        "current_assignments": current_assignments,
    }
    return render(request, "submissions/pool/assignments.html", context)


@login_required
@fellowship_or_admin_required()
def editorial_page(request, identifier_w_vn_nr):
    """Detail page of a Submission its editorial tasks.

    The central page for the Editor-in-charge to manage all its Editorial duties. It's accessible
    for both the Editor-in-charge of the Submission and the Editorial Administration.
    """
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user, latest=False, historical=True),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )

    full_access = True
    if not request.user.has_perm("scipost.can_oversee_refereeing"):
        # Administrators will be able to see all Submissions
        if submission.editor_in_charge != request.user.contributor:
            # The current user is not EIC of the Submission!
            full_access = False

    context = {
        "submission": submission,
        "set_deadline_form": SetRefereeingDeadlineForm(),
        "cycle_choice_form": SubmissionCycleChoiceForm(instance=submission),
        "full_access": full_access,
    }
    return render(request, "submissions/pool/editorial_page.html", context)


@login_required
@fellowship_or_admin_required()
def cycle_form_submit(request, identifier_w_vn_nr):
    """
    Form view to choose refereeing cycle.

    If Submission is a resubmission, the EIC should first choose a refereeing cycle.

    Accessible to: Editor-in-charge and Editorial Administration
    """
    submission = get_object_or_404(
        Submission.objects.in_pool_filter_for_eic(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )

    form = SubmissionCycleChoiceForm(request.POST or None, instance=submission)
    if form.is_valid():
        submission = form.save()
        submission.cycle.reset_refereeing_round()
        messages.success(
            request,
            (
                "<h3>Your choice has been confirmed</h3>"
                "The new cycle will be <em>%s</em>"
                % submission.get_refereeing_cycle_display()
            ),
        )
        if submission.refereeing_cycle == CYCLE_DIRECT_REC:
            # Redirect to EIC Recommendation page immediately
            return redirect(
                reverse(
                    "submissions:eic_recommendation",
                    args=[submission.preprint.identifier_w_vn_nr],
                )
            )
        else:
            # Reinvite only if not direct-cycle.
            submission.cycle.reinvite_referees(form.cleaned_data["referees_reinvite"])
            submission.add_general_event(
                "Referees have been reinvited for the new refereeing cycle."
            )
    return redirect(
        reverse(
            "submissions:editorial_page", args=[submission.preprint.identifier_w_vn_nr]
        )
    )


@permission_required_htmx(
    "scipost.can_invite_referees",
    "You do not have permission to invite referees.",
)
def _hx_select_referee_table(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission,
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )

    # Guard against non-admin and non-EIC users
    is_eic_for_submission = submission.editor_in_charge == request.user.contributor
    can_oversee_refereeing = request.user.has_perm("scipost.can_oversee_refereeing")
    is_admin = request.user.is_staff
    if not (is_eic_for_submission or can_oversee_refereeing or is_admin):
        raise PermissionDenied()

    form = InviteRefereeSearchFrom(
        request.POST or None,
        submission=submission,
        session_key=request.session.session_key,
    )
    if form.is_valid():
        profiles = form.search_results()
    else:
        profiles = Profile.objects.all()

    profiles = profiles.prefetch_related("emails").select_related("contributor")

    paginator = Paginator(profiles, 16)
    page_nr = request.GET.get("page")
    page_obj = paginator.get_page(page_nr)
    count = paginator.count
    start_index = page_obj.start_index
    context = {
        "submission": submission,
        "count": count,
        "page_obj": page_obj,
        "start_index": start_index,
    }
    return render(request, "submissions/_hx_select_referee_table.html", context)


def _hx_select_referee_search_form(request, identifier_w_vn_nr, filter_set: str):
    submission = get_object_or_404(
        Submission,
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )

    # Guard against non-admin and non-EIC users
    is_eic_for_submission = submission.editor_in_charge == request.user.contributor
    can_oversee_refereeing = request.user.has_perm("scipost.can_oversee_refereeing")
    is_admin = request.user.is_staff
    if not (is_eic_for_submission or can_oversee_refereeing or is_admin):
        raise PermissionDenied()

    form = InviteRefereeSearchFrom(
        request.POST or None,
        submission=submission,
        session_key=request.session.session_key,
    )

    if filter_set == "empty":
        form.apply_filter_set(
            {
                "show_email_unknown": True,
                "show_with_CI": True,
                "show_unavailable": True,
            },
            none_on_empty=True,
        )

    context = {"form": form, "submission": submission}
    return render(request, "submissions/_hx_select_referee_search_form.html", context)


@login_required
@fellowship_or_admin_required()
def select_referee(request, identifier_w_vn_nr):
    """
    Search for a referee in the set of Profiles, and if none is found,
    create a new Profile and return to this page for further processing.
    """
    submission: Submission = get_object_or_404(
        Submission.objects.in_pool_filter_for_eic(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )

    if not submission.is_open_for_reporting_within_deadline:
        txt = (
            "The refereeing deadline has passed. You cannot invite a referee anymore."
            " Please, first extend the deadline of the refereeing to invite a referee."
        )
        messages.error(request, txt)
        return redirect(
            reverse(
                "submissions:editorial_page",
                args=(submission.preprint.identifier_w_vn_nr,),
            )
        )

    # If an explicit refereeing deadline does not exist, assume the cycle's default deadline
    refereeing_deadline = (
        submission.reporting_deadline
        or submission.cycle.get_default_refereeing_deadline()
    )

    context = {
        "submission": submission,
        "new_profile_form": SimpleProfileForm(),
        "workdays_left_to_report": workdays_between(
            timezone.now(), refereeing_deadline
        ),
    }
    return render(request, "submissions/select_referee.html", context)


def _hx_customize_refereeing_invitation(request, identifier_w_vn_nr, profile_id):
    submission = get_object_or_404(
        Submission.objects.in_pool_filter_for_eic(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    profile = get_object_or_404(Profile, pk=profile_id)

    form = ConfigureRefereeInvitationForm(
        request.POST or None,
        profile=profile,
        submission=submission,
    )

    context = {
        "submission": submission,
        "form": form,
    }

    if request.method == "POST" and form.is_valid():
        return redirect(
            reverse(
                "submissions:invite_referee",
                kwargs={
                    "identifier_w_vn_nr": submission.preprint.identifier_w_vn_nr,
                    "profile_id": profile_id,
                    "profile_email": form.cleaned_data["profile_email"],
                    "auto_reminders_allowed": form.cleaned_data["has_auto_reminders"],
                },
            )
        )

    return render(
        request, "submissions/_hx_customize_refereeing_invitation.html", context
    )


@permission_required_htmx("scipost.can_add_profile_emails")
def _hx_add_referee_profile_email(request, profile_id):
    """
    Add an email address to a Profile from the select referee page.
    """
    profile = get_object_or_404(Profile, pk=profile_id)

    form = AddProfileEmailForm(
        request.POST or None,
        profile=profile,
        request=request,
        hx_attrs={
            "hx-post": reverse(
                "submissions:_hx_add_referee_profile_email",
                kwargs={"profile_id": profile.id},
            ),
            "hx-target": "previous tbody",
            "hx-swap": "beforeend",
        },
        cancel_parent_tag="tr",
    )

    if form.is_valid():
        profile_email = form.save()
        response = TemplateResponse(
            request,
            "submissions/_hx_select_referee_email_table_row.html",
            {"profile_email": profile_email},
        )

        return response

    return render(
        request, "submissions/_hx_customize_refereeing_invitation.html", {"form": form}
    )


@login_required
@fellowship_or_admin_required()
@transaction.atomic
def add_referee_profile(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission.objects.in_pool_filter_for_eic(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    profile_form = SimpleProfileForm(request.POST or None)
    if profile_form.is_valid():
        profile_form.save()
        messages.success(
            request,
            "Profile added, you can now invite this referee using the links above",
        )
    else:
        messages.error(request, "Could not create this Profile")
        for error_messages in profile_form.errors.values():
            messages.warning(request, *error_messages)
    return redirect(
        reverse(
            "submissions:select_referee",
            kwargs={"identifier_w_vn_nr": submission.preprint.identifier_w_vn_nr},
        )
        + ("?last_name=%s" % profile_form.cleaned_data["last_name"])
    )


@login_required
@fellowship_or_admin_required()
@transaction.atomic
def invite_referee(
    request, identifier_w_vn_nr, profile_id, profile_email, auto_reminders_allowed
):
    """
    Invite a referee linked to a Profile using their profile email.
    If the Profile has a Contributor object, a simple invitation is sent.
    If there is no associated Contributor, a registration invitation is included.
    """
    submission = get_object_or_404(
        Submission.objects.in_pool_filter_for_eic(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    profile = get_object_or_404(Profile, pk=profile_id)
    auto_reminders_allowed = auto_reminders_allowed == "True"

    # Guard against profiles who don't want to referee
    if not profile.accepts_refereeing_requests:
        messages.error(
            request,
            "This person has indicated that they do not want to be invited to referee.",
        )
        return redirect(
            reverse(
                "submissions:editorial_page",
                kwargs={"identifier_w_vn_nr": identifier_w_vn_nr},
            )
        )

    # Guard against already invited referees
    if (
        RefereeInvitation.objects.filter(
            referee=profile, submission=submission, cancelled=False
        )
        .exclude(email_address=profile_email)
        .exists()
    ):
        messages.error(
            request,
            "This referee has already been invited.",
        )
        return redirect(
            reverse(
                "submissions:editorial_page",
                kwargs={"identifier_w_vn_nr": identifier_w_vn_nr},
            )
        )

    # Guard against profiles with competing interests
    if not (
        Profile.objects.filter(pk=profile.pk)
        .without_competing_interests_against_submission_authors_of(submission)
        .exists()
    ):
        messages.error(
            request,
            "This Profile has a competing interest with the authors of the Submission.",
        )
        return redirect(
            reverse(
                "submissions:editorial_page",
                kwargs={"identifier_w_vn_nr": identifier_w_vn_nr},
            )
        )

    contributor = None
    if hasattr(profile, "contributor") and profile.contributor:
        contributor = profile.contributor

    has_agreed_to_previous_invitation = RefereeInvitation.objects.filter(
        referee=profile, submission__thread_hash=submission.thread_hash, accepted=True
    ).exists()

    # Guard against profiles who are not currently available
    if (
        contributor is not None
        and not contributor.is_currently_available
        and not has_agreed_to_previous_invitation
    ):
        error_message = (
            "This referee is not currently available, "
            "and has not accepted a previous invitation for this submission."
        )
        return render(request, "scipost/error.html", {"errormessage": error_message})

    # We cannot proceed if the Profile has no email address
    # or if the email address is not linked to the Profile.
    profile_email = profile.emails.get(email=profile_email)
    if profile_email is None:
        raise Http404

    referee_invitation, created = RefereeInvitation.objects.get_or_create(
        referee=profile,
        submission=submission,
        email_address=profile_email.email,
        auto_reminders_allowed=auto_reminders_allowed,
        invited_by=request.user.contributor,
    )

    key = ""
    if created:
        key = get_new_secrets_key()
        referee_invitation.invitation_key = key
        referee_invitation.save()
    elif referee_invitation.cancelled:
        referee_invitation.cancelled = False
        referee_invitation.save()

    registration_invitation = None

    if contributor is not None:
        mail_request = MailEditorSubview(
            request,
            mail_code="referees/invite_contributor_to_referee",
            invitation=referee_invitation,
        )
    else:  # no Contributor, so registration invitation
        registration_invitation, reginv_created = (
            RegistrationInvitation.objects.get_or_create(
                profile=profile,
                title=profile.title if profile.title else TITLE_DR,
                first_name=profile.first_name,
                last_name=profile.last_name,
                email=profile_email.email,
                invitation_type=INVITATION_REFEREEING,
                created_by=request.user,
                invited_by=request.user,
                invitation_key=referee_invitation.invitation_key,
            )
        )
        mail_request = MailEditorSubview(
            request,
            mail_code="referees/invite_unregistered_to_referee",
            invitation=referee_invitation,
        )

    if mail_request.is_valid():
        referee_invitation.date_invited = timezone.now()
        referee_invitation.save()
        if registration_invitation:
            registration_invitation.status = STATUS_SENT
            registration_invitation.key_expires = timezone.now() + datetime.timedelta(
                days=365
            )
            registration_invitation.save()
        submission.add_event_for_author("A referee has been invited.")
        submission.add_event_for_eic("Referee %s has been invited." % profile.last_name)
        messages.success(request, "Invitation sent")
        mail_request.send_mail()
        return redirect(
            reverse(
                "submissions:editorial_page",
                kwargs={"identifier_w_vn_nr": identifier_w_vn_nr},
            )
        )
    else:
        return mail_request.interrupt()


@transaction.atomic
def _hx_quick_invite_referee(request, identifier_w_vn_nr, profile_id):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    profile = get_object_or_404(Profile, pk=profile_id)

    # Guard against non-admin and non-EIC users
    is_eic_for_submission = submission.editor_in_charge == request.user.contributor
    can_oversee_refereeing = request.user.has_perm("scipost.can_oversee_refereeing")
    if not (is_eic_for_submission or can_oversee_refereeing):
        return HTMXPermissionsDenied("You do not have permission to invite referees.")

    # Guard against profiles who don't want to referee
    if not profile.accepts_refereeing_requests:
        return HTMXResponse(
            "This person has indicated that they do not want to be invited to referee.",
            tag="danger",
        )

    # Guard against already invited referees
    if RefereeInvitation.objects.filter(
        referee=profile, submission=submission, cancelled=False
    ).exists():
        return HTMXResponse(
            "This referee has already been invited.",
            tag="danger",
        )

    # Guard against profiles with competing interests
    if not (
        Profile.objects.filter(pk=profile.pk)
        .without_competing_interests_against_submission_authors_of(submission)
        .exists()
    ):
        return HTMXResponse(
            "This Profile has a competing interest with the authors of the Submission.",
            tag="danger",
        )

    contributor = None
    if hasattr(profile, "contributor") and profile.contributor:
        contributor = profile.contributor

    has_agreed_to_previous_invitation = RefereeInvitation.objects.filter(
        referee=profile, submission__thread_hash=submission.thread_hash, accepted=True
    ).exists()

    # Guard against profiles who are not currently available
    if (
        contributor is not None
        and not contributor.is_currently_available
        and not has_agreed_to_previous_invitation
    ):
        return HTMXResponse(
            "This referee is not currently available, "
            "and has not accepted a previous invitation for this submission.",
            tag="danger",
        )

    primary_or_first_email = profile.emails.order_by("-primary").first().email
    referee_invitation, created = RefereeInvitation.objects.get_or_create(
        referee=profile,
        submission=submission,
        email_address=primary_or_first_email,
        auto_reminders_allowed=True,
        invited_by=request.user.contributor,
    )

    key = ""
    if created:
        key = get_new_secrets_key()
        referee_invitation.invitation_key = key
        referee_invitation.save()
    elif referee_invitation.cancelled:
        referee_invitation.cancelled = False
        referee_invitation.save()

    registration_invitation = None

    if contributor is not None:
        mail_request = DirectMailUtil(
            "referees/invite_contributor_to_referee",
            invitation=referee_invitation,
        )
    else:  # no Contributor, so registration invitation
        registration_invitation, reginv_created = (
            RegistrationInvitation.objects.get_or_create(
                profile=profile,
                title=profile.title if profile.title else TITLE_DR,
                first_name=profile.first_name,
                last_name=profile.last_name,
                email=profile.email,
                invitation_type=INVITATION_REFEREEING,
                created_by=request.user,
                invited_by=request.user,
                invitation_key=referee_invitation.invitation_key,
            )
        )
        mail_request = DirectMailUtil(
            mail_code="referees/invite_unregistered_to_referee",
            invitation=referee_invitation,
        )

    mail_request.send_mail()

    referee_invitation.date_invited = timezone.now()
    referee_invitation.save()
    if registration_invitation:
        registration_invitation.status = STATUS_SENT
        registration_invitation.key_expires = timezone.now() + datetime.timedelta(
            days=365
        )
        registration_invitation.save()

    submission.add_event_for_author("A referee has been invited.")
    submission.add_event_for_eic("Referee %s has been invited." % profile.last_name)

    return HTMXResponse("Invitation sent", tag="success")


@login_required
@fellowship_or_admin_required()
def set_refinv_auto_reminder(request, invitation_id, auto_reminders):
    """Set the value of the Boolean for automatic refereeing reminders."""
    invitation = get_object_or_404(RefereeInvitation, pk=invitation_id)
    if auto_reminders == 0:
        invitation.auto_reminders_allowed = False
        messages.success(request, "Auto reminders succesfully turned off.")
    elif auto_reminders == 1:
        invitation.auto_reminders_allowed = True
        messages.success(request, "Auto reminders succesfully turned on.")
    else:
        messages.warning(request, "Option not recognized.")
    invitation.save()
    return redirect(
        reverse(
            "submissions:editorial_page",
            kwargs={
                "identifier_w_vn_nr": invitation.submission.preprint.identifier_w_vn_nr
            },
        )
    )


@login_required
@fellowship_or_admin_required()
def ref_invitation_reminder(request, identifier_w_vn_nr, invitation_id):
    """Send reminder email to pending RefereeInvitations.

    This method is used by the Editor-in-charge from the editorial_page
    when a referee has been invited but hasn't answered yet.
    It can be used for registered as well as unregistered referees.

    Accessible for: Editor-in-charge and Editorial Administration
    """
    submission = get_object_or_404(
        Submission.objects.in_pool_filter_for_eic(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    invitation: "RefereeInvitation" = get_object_or_404(
        submission.referee_invitations.all(), pk=invitation_id
    )
    invitation.reminder_sent()

    SubmissionUtils.load({"invitation": invitation}, request)
    if invitation.to_registered_referee:
        SubmissionUtils.send_ref_reminder_email()
    else:
        SubmissionUtils.send_unreg_ref_reminder_email()
    messages.success(request, "Reminder sent successfully.")
    return redirect(
        reverse(
            "submissions:editorial_page",
            kwargs={"identifier_w_vn_nr": identifier_w_vn_nr},
        )
    )


@login_required
@permission_required("scipost.can_referee", raise_exception=True)
def accept_or_decline_ref_invitations(request, invitation_id=None):
    """Decide on RefereeInvitation.

    RefereeInvitations need to be either accepted or declined by the invited user
    using this view. The decision will be taken one invitation at a time.
    """
    invitation = RefereeInvitation.objects.awaiting_response().filter(
        referee=request.user.contributor.profile
    )
    if invitation_id:
        try:
            invitation = invitation.get(id=invitation_id)
        except RefereeInvitation.DoesNotExist:
            invitation = invitation.first()
    else:
        invitation = invitation.first()

    if not isinstance(invitation, RefereeInvitation):
        messages.success(
            request, "There are no more Refereeing Invitations for you to consider."
        )
        return redirect(reverse("scipost:personal_page"))

    form = ConsiderRefereeInvitationForm(request.POST or None, invitation=invitation)
    if form.is_valid():
        invitation = form.save(commit=False)
        invitation.date_responded = timezone.now()
        if form.cleaned_data["accept"] == "True":
            invitation.accepted = True
            decision_string = "accepted"
            messages.success(
                request,
                (
                    "<h3>Thank you for agreeing to referee this Submission</h3>"
                    "<p>When you are ready, please go to the "
                    '<a href="{url}">Submission\'s page</a> to'
                    " submit your Report.</p>".format(
                        url=invitation.submission.get_absolute_url()
                    )
                ),
            )

            # Set the refereeing cycle's deadline to the cycle's default
            # if it is not set yet.
            if invitation.submission.reporting_deadline is None:
                invitation.submission.reporting_deadline = (
                    invitation.submission.cycle.get_default_refereeing_deadline()
                )
                invitation.submission.save()

        else:
            invitation.accepted = False
            decision_string = "declined"
            invitation.refusal_reason = form.cleaned_data["refusal_reason"]
            invitation.other_refusal_reason = form.cleaned_data["other_refusal_reason"]
            messages.success(
                request,
                (
                    "<h3>You have declined to contribute a Report</h3>"
                    "Nonetheless, we thank you very much for considering"
                    " this refereeing invitation.</p>"
                ),
            )
        invitation.save()

        if invitation.accepted:
            subject_eic = "SciPost: Referee accepts to review"
            subject_referee = "SciPost: Confirmation accepted invitation"
        else:
            subject_eic = "SciPost: Referee declines to review"
            subject_referee = "SciPost: Confirmation declined invitation"
        mail_util = DirectMailUtil(
            "eic/referee_response", invitation=invitation, subject=subject_eic
        )
        mail_util.send_mail()
        mail_util = DirectMailUtil(
            "referees/confirmation_invitation_response",
            invitation=invitation,
            subject=subject_referee,
        )

        # Add SubmissionEvents
        invitation.submission.add_event_for_author(
            "A referee has %s the refereeing invitation." % decision_string
        )
        invitation.submission.add_event_for_eic(
            "Referee %s has %s the refereeing invitation."
            % (invitation.referee.full_name, decision_string)
        )

        if request.user.contributor.profile.referee_invitations.awaiting_response().exists():
            return redirect("submissions:accept_or_decline_ref_invitations")
        return redirect(invitation.submission.get_absolute_url())
    context = {"invitation": invitation, "form": form}
    return render(request, "submissions/referee_invitations_form.html", context)


def decline_ref_invitation(request, invitation_key):
    """Decline a RefereeInvitation."""
    invitation = get_object_or_404(
        RefereeInvitation.objects.awaiting_response().non_cancelled(),
        invitation_key=invitation_key,
    )

    # Push the invitation to the user's session
    # for use with refereeing indications later
    request.session["invitation_key"] = invitation_key

    form = ConsiderRefereeInvitationForm(
        request.POST or None, initial={"accept": False}
    )
    context = {"invitation": invitation, "form": form}
    if form.is_valid():
        if form.cleaned_data["accept"] == "True":
            # User filled in: Accept
            messages.warning(
                request,
                "Please login and go to your personal page if you"
                " want to accept the invitation.",
            )
            return render(
                request, "submissions/referee_invitations_decline.html", context
            )

        invitation.accepted = False
        invitation.date_responded = timezone.now()
        invitation.refusal_reason = form.cleaned_data["refusal_reason"]
        invitation.other_refusal_reason = form.cleaned_data["other_refusal_reason"]
        invitation.save()

        mail_util = DirectMailUtil(
            "eic/referee_response",
            invitation=invitation,
            subject="SciPost: Referee declines to review",
        )
        mail_util.send_mail()

        # Add SubmissionEvents
        invitation.submission.add_event_for_author(
            "A referee has declined the refereeing invitation."
        )
        invitation.submission.add_event_for_eic(
            "Referee %s has declined the refereeing "
            "invitation." % invitation.referee.full_name
        )

        messages.success(
            request, "Thank you for informing us that you will not provide a Report."
        )
        return redirect(reverse("scipost:index"))
    return render(request, "submissions/referee_invitations_decline.html", context)


@login_required
def _hx_cancel_ref_invitation(request, identifier_w_vn_nr, invitation_id):
    """Cancel a RefereeInvitation.

    This method is used by the Editor-in-charge from the editorial_page to remove a referee
    from the list of invited ones. It can be used for registered as well as unregistered referees.

    Accessible for: Editor-in-charge and Editorial Administration.
    """
    try:
        submissions = Submission.objects.in_pool_filter_for_eic(request.user)
        invitation = RefereeInvitation.objects.get(
            submission__in=submissions, pk=invitation_id
        )
    except RefereeInvitation.DoesNotExist:
        return HTMXResponse("Invitation not found/accessible", tag="danger")

    if invitation.fulfilled:
        return HTMXResponse("Invitation already fulfilled", tag="danger")
    elif invitation.cancelled:
        return HTMXResponse("Invitation already cancelled", tag="danger")
    elif invitation.accepted == False:
        return HTMXResponse("Invitation already declined.", tag="danger")

    invitation.cancelled = True
    invitation.save()

    notify_by_email = request.GET.get("notify_by_email", False)
    if notify_by_email:
        SubmissionUtils.load({"invitation": invitation})
        if invitation.date_invited is not None:
            SubmissionUtils.send_ref_cancellation_email()

    # Add SubmissionEvents
    invitation.submission.add_event_for_author(
        "A referee invitation has been cancelled."
    )
    invitation.submission.add_event_for_eic(
        "Referee invitation for %s has been cancelled." % invitation.referee.full_name
    )

    return HTMXResponse("Invitation cancelled", tag="success")


def _hx_report_intended_delivery_form(request, invitation_id):
    """
    Render the form to edit the intended delivery date of a referee report.
    Only invited referees and EIC can access this form.
    """
    invitation = get_object_or_404(RefereeInvitation, pk=invitation_id)

    is_invited_referee = invitation.referee == request.user.contributor.profile
    is_editor = invitation.submission.editor_in_charge == request.user.contributor
    if not (is_invited_referee or is_editor):
        return HTMXPermissionsDenied(
            "You do not have permission to edit the intended delivery date."
        )

    if invitation.fulfilled:
        return HTMXResponse(
            "The report has already been delivered. You may not change the intended delivery date.",
            tag="danger",
        )
    if invitation.cancelled:
        return HTMXResponse(
            "The invitation has been cancelled. You may not change the intended delivery date.",
            tag="danger",
        )

    form = ReportIntendedDeliveryForm(request.POST or None, instance=invitation)

    if form.is_valid():
        invitation = form.save()
        messages.success(
            request,
            f"Intended delivery date updated to {invitation.intended_delivery_date}.",
        )
        return HttpResponse(
            '<a class="d-inline-block" hx-get="{url}">Change intended delivery date</a>'.format(
                url=reverse_lazy(
                    "submissions:_hx_report_intended_delivery_form",
                    kwargs={"invitation_id": invitation_id},
                )
            )
        )
    context = {"invitation": invitation, "form": form}
    return render(request, "htmx/crispy_form.html", context)


@login_required
def extend_refereeing_deadline(request, identifier_w_vn_nr, days):
    """
    Extend Refereeing deadline for Submission and open reporting and commenting.

    Accessible for: Editor-in-charge and Editorial Administration
    """
    submission = get_object_or_404(
        Submission.objects.in_pool_filter_for_eic(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )

    # Guard against null reporting_deadline
    if submission.reporting_deadline is None:
        messages.warning(request, "Reporting deadline is not set.")
        return redirect(
            reverse(
                "submissions:editorial_page",
                kwargs={"identifier_w_vn_nr": identifier_w_vn_nr},
            )
        )

    Submission.objects.filter(pk=submission.id).update(
        reporting_deadline=submission.reporting_deadline
        + datetime.timedelta(days=int(days)),
        open_for_reporting=True,
        open_for_commenting=True,
        latest_activity=timezone.now(),
    )
    submission.refresh_from_db()

    messages.success(
        request,
        "Refereeing deadline set to {0}.".format(
            submission.reporting_deadline.strftime("%Y-%m-%d")
        ),
    )

    submission.add_general_event("A new refereeing deadline is set.")
    return redirect(
        reverse(
            "submissions:editorial_page",
            kwargs={"identifier_w_vn_nr": identifier_w_vn_nr},
        )
    )


@login_required
def set_refereeing_deadline(request, identifier_w_vn_nr):
    """Set Refereeing deadline for Submission and open reporting and commenting.

    Accessible for: Editor-in-charge and Editorial Administration
    """
    submission = get_object_or_404(
        Submission.objects.in_pool_filter_for_eic(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )

    if not submission.can_reset_reporting_deadline:
        # Protect eg. published submissions.
        messages.warning(request, "Reporting deadline can not be reset.")
        return redirect(
            reverse(
                "submissions:editorial_page",
                kwargs={"identifier_w_vn_nr": identifier_w_vn_nr},
            )
        )

    form = SetRefereeingDeadlineForm(request.POST or None)
    if form.is_valid():
        Submission.objects.filter(pk=submission.id).update(
            reporting_deadline=form.cleaned_data["deadline"],
            open_for_reporting=True,
            latest_activity=timezone.now(),
        )
        submission.refresh_from_db()
        submission.add_general_event("A new refereeing deadline is set.")
        messages.success(
            request,
            "New reporting deadline set to %s." % submission.reporting_deadline.date(),
        )
    else:
        messages.error(
            request, "The deadline has not been set: %s Please try again." % form.errors
        )

    return redirect(
        reverse(
            "submissions:editorial_page",
            kwargs={"identifier_w_vn_nr": identifier_w_vn_nr},
        )
    )


@login_required
def close_refereeing_round(request, identifier_w_vn_nr):
    """Close Submission for refereeing.

    Called by the Editor-in-charge when a satisfactory number of reports have been gathered.
    Automatically emails the authors to ask them if they want to round off any replies to
    reports or comments before the editorial recommendation is formulated.

    Accessible for: Editor-in-charge and Editorial Administration.
    """
    submission = get_object_or_404(
        Submission.objects.in_pool_filter_for_eic(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )

    Submission.objects.filter(id=submission.id).update(
        open_for_reporting=False,
        open_for_commenting=False,
        reporting_deadline=timezone.now(),
        latest_activity=timezone.now(),
    )
    submission.add_general_event("Refereeing round has been closed.")
    messages.success(request, "Refereeing round closed.")

    return redirect(
        reverse(
            "submissions:editorial_page",
            kwargs={"identifier_w_vn_nr": identifier_w_vn_nr},
        )
    )


@permission_required("scipost.can_oversee_refereeing", raise_exception=True)
def refereeing_overview(request):
    """List all Submissions undergoing active Refereeing."""
    submissions_under_refereeing = (
        Submission.objects.in_pool(request.user)
        .in_refereeing()
        .order_by("submission_date")
    )
    context = {"submissions_under_refereeing": submissions_under_refereeing}
    return render(request, "submissions/admin/refereeing_overview.html", context)


@login_required
def communication(request, identifier_w_vn_nr, comtype, referee_id=None):
    """Send refereeing related communication.

    Communication may be between two of: editor-in-charge, author and referee.
    """
    referee = None
    author_letter, recipient_letter = re.match(r"(\w)to(\w)", comtype).groups()

    valid_comtypes = [comtype[0] for comtype in ED_COMM_CHOICES]

    # Referee to Author communication is strictly forbidden
    valid_comtypes.remove("RtoA")
    valid_comtypes.remove("AtoR")

    if comtype not in valid_comtypes:
        raise Http404("Invalid communication type")

    match author_letter:
        case "A":
            submissions_qs = Submission.objects.filter_for_author(request.user)
        case "E":
            submissions_qs = Submission.objects.in_pool_filter_for_eic(
                request.user,
                latest=False,
                historical=True,
            )
        case "R":
            submissions_qs = Submission.objects.filter(
                referee_invitations__referee=request.user.contributor.profile
            )
            referee = request.user.contributor.profile
        case "S":
            if not request.user.has_perm("scipost.can_oversee_refereeing"):
                raise PermissionDenied
            submissions_qs = Submission.objects.in_pool(
                request.user,
                historical=True,
            )
            referee = request.user.contributor.profile
        case _:
            # Invalid author letter
            raise Http404("Invalid author letter")

    # Uniquify and get the showpiece itself or return 404
    submission = get_object_or_404(
        submissions_qs.distinct(), preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )

    print(recipient_letter, referee_id)
    if recipient_letter == "R" and referee_id:
        # Get the Contributor to communicate with if not already defined (`Eto?` communication)
        # To Fix: Assuming the Editorial Administrator won't make any `referee_id` mistakes
        if invitation := RefereeInvitation.objects.filter(
            submission__thread_hash=submission.thread_hash,
            referee__id=referee_id,
        ).first():
            referee = invitation.referee

    dummy_communication = EditorialCommunication(
        comtype=comtype, submission=submission, referee=referee
    )
    form = EditorialCommunicationForm(request.POST or None)
    if form.is_valid():
        communication = form.save(commit=False)
        communication.submission = submission
        communication.comtype = comtype
        communication.referee = referee
        communication.save()

        try:
            SubmissionUtils.load({"communication": communication})
            SubmissionUtils.send_communication_email()
        except Exception as e:
            messages.error(
                request,
                "Communication submitted, but an error occurred while sending the email: "
                + str(e),
            )
            sentry_sdk.capture_exception(e)
            return redirect(submission.get_absolute_url())

        messages.success(request, "Communication submitted")
        if author_letter == "E":
            return redirect(
                reverse(
                    "submissions:editorial_page",
                    kwargs={"identifier_w_vn_nr": identifier_w_vn_nr},
                )
            )
        elif author_letter == "A":
            return redirect(submission.get_absolute_url())
        elif author_letter == "S":
            return redirect(reverse("submissions:pool:pool"))
        return redirect(submission.get_absolute_url())

    context = {
        "submission": submission,
        "comtype": comtype,
        "referee_id": referee_id,
        "form": form,
        "dummy_communication": dummy_communication,
    }
    return render(request, "submissions/communication.html", context)


@login_required
@fellowship_or_admin_required()
def reset_refereeing_cycle(request, identifier_w_vn_nr):
    """Reset the refereeing cycle for a Submission.

    Accessible for: Editor-in-charge and Editorial Administration
    """
    submission: "Submission" = get_object_or_404(
        Submission.objects.in_pool_filter_for_eic(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )

    submission.reset_refereeing_cycle()

    messages.success(request, "Refereeing cycle has been reset.")

    submission.add_event_for_eic("The refereeing cycle has been reset.")
    return redirect(
        reverse(
            "submissions:editorial_page",
            kwargs={"identifier_w_vn_nr": identifier_w_vn_nr},
        )
    )


@login_required
@fellowship_or_admin_required()
@transaction.atomic
def _hx_eic_recommendation_form(request, identifier_w_vn_nr):
    """
    Handle the EIC Recommendation form submission.
    """
    submission = get_object_or_404(
        Submission.objects.in_pool_filter_for_eic(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )

    form = EICRecommendationForm(request.POST or None, submission=submission)

    if form.is_valid():
        recommendation = form.save()
        if form.revision_requested():
            # Send mail to authors to notify about the request for revision.
            SubmissionUtils.load(
                {
                    "submission": form.submission,
                    "recommendation": recommendation,
                }
            )
            SubmissionUtils.send_author_revision_requested_email()

        response = HttpResponse()
        messages.success(request, "Editorial Recommendation successfully formulated")
        response["HX-Redirect"] = reverse(
            "submissions:editorial_page",
            kwargs={"identifier_w_vn_nr": identifier_w_vn_nr},
        )
        return response

    context = {"submission": submission, "form": form}
    return render(request, "submissions/pool/_hx_eic_recommendation_form.html", context)


@login_required
@fellowship_or_admin_required()
@transaction.atomic
def eic_recommendation(request, identifier_w_vn_nr):
    """Write EIC Recommendation.

    Accessible for: Editor-in-charge and Editorial Administration
    """
    submission = get_object_or_404(
        Submission.objects.in_pool_filter_for_eic(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )

    if not submission.eic_recommendation_required:
        messages.warning(
            request,
            (
                "<h3>An Editorial Recommendation is not required</h3>"
                "This submission's current status is: <em>%s</em>"
                % submission.get_status_display()
            ),
        )
        return redirect(
            reverse(
                "submissions:editorial_page",
                args=[submission.preprint.identifier_w_vn_nr],
            )
        )

    form = EICRecommendationForm(request.POST or None, submission=submission)
    # Find EditorialAssignment for user
    if not form.has_assignment():
        messages.warning(
            request,
            (
                "You cannot formulate an Editorial Recommendation,"
                " because the Editorial Assignment has not been set properly."
                " Please contact EdAdmin to report the problem."
            ),
        )
        return redirect(
            reverse(
                "submissions:editorial_page",
                args=[submission.preprint.identifier_w_vn_nr],
            )
        )

    context = {"submission": submission, "form": form}
    return render(request, "submissions/pool/recommendation_formulate.html", context)


@login_required
@fellowship_or_admin_required()
@transaction.atomic
def reformulate_eic_recommendation(request, identifier_w_vn_nr):
    """Reformulate EIC Recommendation form view.

    Accessible for: Editor-in-charge and Editorial Administration.
    """
    submission = get_object_or_404(
        Submission.objects.in_pool_filter_for_eic(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    recommendation = submission.eicrecommendations.last()
    if not recommendation:
        raise Http404("No EICRecommendation formulated yet.")

    if not recommendation.may_be_reformulated:
        messages.warning(
            request,
            (
                "With the current status of the EICRecommendation you are not "
                "allowed to reformulate the Editorial Recommendation"
            ),
        )
        return redirect(
            reverse("submissions:editorial_page", args=(identifier_w_vn_nr,))
        )

    form = EICRecommendationForm(
        request.POST or None, submission=submission, reformulate=True
    )
    context = {"submission": submission, "form": form}
    return render(
        request, "submissions/pool/recommendation_formulate_rewrite.html", context
    )


###########
# Reports
###########
@login_required
@permission_required("scipost.can_referee", raise_exception=True)
@transaction.atomic
def submit_report(request, identifier_w_vn_nr):
    """Submit Report on a Submission.

    Important checks to be aware of include an author check for the submission,
    has the reporting deadline not been reached yet and does there exist any invitation
    for the current user on this submission.
    """
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )

    # Check whether the user can submit a report:
    is_author = check_verified_author(submission, request.user)
    is_author_unchecked = check_unverified_author(submission, request.user)
    invitation = submission.referee_invitations.filter(
        fulfilled=False, cancelled=False, referee=request.user.contributor.profile
    ).first()

    errormessage = None
    if is_author:
        errormessage = (
            "You are an author of this Submission and cannot submit a Report."
        )
    elif is_author_unchecked:
        errormessage = (
            "The system flagged you as a potential author of this Submission. "
            "Please go to your personal page under the Submissions tab"
            " to clarify this."
        )
    elif not invitation:
        # User is going to contribute a Report. Check deadlines for doing so.
        # Allow post-deadline reporting:
        # if timezone.now() > submission.reporting_deadline + datetime.timedelta(days=1):
        #     errormessage = ('The reporting deadline has passed. You cannot submit'
        #                     ' a Report anymore.')
        if not submission.open_for_reporting:
            errormessage = (
                "Reporting for this submission has closed. You cannot submit"
                " a Report anymore."
            )

        if errormessage:
            # Remove old drafts from the database
            submission.reports.in_draft().filter(author__dbuser=request.user).delete()

    if errormessage:
        messages.warning(request, errormessage)
        return redirect(submission.get_absolute_url())

    # Find and fill earlier version of report
    try:
        report_in_draft = submission.reports.in_draft().get(author__dbuser=request.user)
    except Report.DoesNotExist:
        report_in_draft = Report(author=request.user.contributor, submission=submission)
    form = ReportForm(
        request.POST or None,
        request.FILES or None,
        instance=report_in_draft,
        submission=submission,
        request=request,
    )

    # Check if data sent is valid
    if form.is_valid():
        newreport = form.save()
        if newreport.status == STATUS_DRAFT:
            messages.success(
                request,
                (
                    "Your Report has been saved. "
                    "You may carry on working on it,"
                    " or leave the page and finish it later."
                ),
            )
            context = {"submission": submission, "form": form}
            return redirect(
                reverse(
                    "submissions:submit_report",
                    kwargs={"identifier_w_vn_nr": identifier_w_vn_nr},
                )
            )

        # Send mails if report is submitted
        mail_sender = DirectMailUtil(
            "referees/inform_referee_report_received", report=newreport
        )
        mail_sender.send_mail()
        mail_sender = DirectMailUtil("eic/inform_eic_report_received", report=newreport)
        mail_sender.send_mail()

        # Add SubmissionEvents for the EIC only, as it can also be rejected still
        submission.add_event_for_eic(
            "%s has submitted a new Report." % request.user.last_name
        )

        messages.success(request, "Thank you for your Report")
        return redirect(submission.get_absolute_url())
    elif request.POST:
        messages.error(request, "Report not submitted, please read the errors below.")

    context = {"submission": submission, "form": form}
    return render(request, "submissions/report_form.html", context)


@login_required
@fellowship_or_admin_required()
def vet_submitted_reports_list(request):
    """List Reports with status `unvetted`."""
    submissions = get_list_or_404(
        Submission.objects.in_pool_filter_for_eic(request.user)
    )
    reports_to_vet = (
        Report.objects.filter(submission__in=submissions)
        .awaiting_vetting()
        .order_by("date_submitted")
    )
    context = {"reports_to_vet": reports_to_vet}
    return render(request, "submissions/vet_submitted_reports_list.html", context)


@login_required
@fellowship_or_admin_required()
@transaction.atomic
def vet_submitted_report(request, report_id):
    """List Reports with status `unvetted` for vetting purposes.

    A user may only vet reports of submissions they are EIC of or if they are
    SciPost Administratoror Vetting Editor.

    After vetting an email is sent to the report author, bcc EIC. If report
    has not been refused, the submission author is also mailed.
    """
    if request.user.has_perm("scipost.can_vet_submitted_reports"):
        # Vetting Editors may vote on everything.
        report = get_object_or_404(Report.objects.awaiting_vetting(), id=report_id)
    else:
        submissions = Submission.objects.in_pool_filter_for_eic(
            request.user, latest=False, historical=True
        )
        report = get_object_or_404(
            Report.objects.filter(submission__in=submissions).awaiting_vetting(),
            id=report_id,
        )

    form = VetReportForm(request.POST or None, report=report)
    if form.is_valid():
        report = form.process_vetting(request.user.contributor)

        # email report author
        SubmissionUtils.load(
            {
                "report": report,
                "email_response": form.cleaned_data["email_response_field"],
            }
        )
        SubmissionUtils.acknowledge_report_email()  # email report author, bcc EIC

        # Add SubmissionEvent for the EIC
        report.submission.add_event_for_eic(
            "The Report by %s is vetted." % report.author.user.last_name
        )
        if report.status == STATUS_VETTED:
            SubmissionUtils.send_author_report_received_email()

            # Add SubmissionEvent to tell the author about the new report
            report.submission.add_event_for_author("A new Report has been submitted.")

        message = 'Submitted Report vetted for <a href="{url}">{arxiv}</a>.'.format(
            url=report.submission.get_absolute_url(),
            arxiv=report.submission.preprint.identifier_w_vn_nr,
        )
        messages.success(request, message)

        if report.submission.editor_in_charge == request.user.contributor:
            # Redirect a EIC back to the Editorial Page!
            return redirect(
                reverse(
                    "submissions:editorial_page",
                    args=(report.submission.preprint.identifier_w_vn_nr,),
                )
            )
        return redirect(reverse("submissions:vet_submitted_reports_list"))

    context = {"report_to_vet": report, "form": form}
    return render(request, "submissions/vet_submitted_report.html", context)


@login_required
@permission_required(
    "scipost.can_prepare_recommendations_for_voting", raise_exception=True
)
@transaction.atomic
def prepare_for_voting(request, rec_id):
    """Form view to prepare a EICRecommendation for voting."""
    submissions = Submission.objects.in_pool(request.user)
    recommendation = get_object_or_404(
        EICRecommendation.objects.voting_in_preparation().filter(
            submission__in=submissions
        ),
        id=rec_id,
    )

    eligibility_form = VotingEligibilityForm(
        request.POST or None, instance=recommendation
    )
    if eligibility_form.is_valid():
        eligibility_form.save()
        messages.success(request, "We have registered your selection.")

        # Add SubmissionEvents
        recommendation.submission.add_event_for_eic(
            "The Editorial Recommendation has been "
            "put forward to the College for voting."
        )

        return redirect(
            reverse(
                "submissions:editorial_page",
                args=[recommendation.submission.preprint.identifier_w_vn_nr],
            )
        )
    else:
        fellows_with_expertise = recommendation.submission.fellows.filter(
            Q(contributor=recommendation.submission.editor_in_charge)
            | Q(
                contributor__profile__specialties__in=recommendation.submission.specialties.all()
            )
        ).order_by("contributor__dbuser__last_name")

        # coauthorships = recommendation.submission.flag_coauthorships_arxiv(fellows_with_expertise)
        coauthorships = None

        prev_elig_id = []
        for prev_rec in recommendation.get_other_versions():
            prev_elig_id += [fellow.id for fellow in prev_rec.eligible_to_vote.all()]
        previously_eligible_for_voting = Contributor.objects.filter(pk__in=prev_elig_id)

    context = {
        "recommendation": recommendation,
        "fellows_with_expertise": fellows_with_expertise,
        "previously_eligible_for_voting": previously_eligible_for_voting,
        "coauthorships": coauthorships,
        "eligibility_form": eligibility_form,
    }
    return render(
        request, "submissions/admin/recommendation_prepare_for_voting.html", context
    )


@login_required
@fellowship_or_admin_required()
def claim_voting_right(request, rec_id):
    """Claim voting right on EICRecommendation."""
    rec = get_object_or_404(EICRecommendation, pk=rec_id)
    granted = False
    if rec.submission.fellows.filter(contributor=request.user.contributor).exists():
        rec.eligible_to_vote.add(request.user.contributor)
        granted = True
    context = {"rec": rec, "granted": granted}
    return render(
        request, "submissions/pool/_hx_recommendation_claim_voting_right.html", context
    )


@login_required
@fellowship_or_admin_required()
@transaction.atomic
def vote_on_rec(request, rec_id):
    """Form view for Fellows to cast their vote on EICRecommendation."""
    submissions = Submission.objects.in_pool(request.user)
    previous_vote = None
    try:
        recommendation = EICRecommendation.objects.user_must_vote_on(request.user).get(
            submission__in=submissions, id=rec_id
        )
        initial = {"vote": "abstain"}
    except EICRecommendation.DoesNotExist:  # Try to find an EICRec already voted on:
        try:
            recommendation = EICRecommendation.objects.user_current_voted(
                request.user
            ).get(submission__in=submissions, id=rec_id)
            if request.user.contributor in recommendation.voted_for.all():
                previous_vote = "agree"
            elif request.user.contributor in recommendation.voted_against.all():
                previous_vote = "disagree"
            elif request.user.contributor in recommendation.voted_abstain.all():
                previous_vote = "abstain"
        except EICRecommendation.DoesNotExist:
            raise Http404

    context = {
        "recommendation": recommendation,
    }
    return render(request, "submissions/pool/recommendation.html", context)


@permission_required(
    "scipost.can_prepare_recommendations_for_voting", raise_exception=True
)
def remind_Fellows_to_vote(request, rec_id):
    """
    Send an email to Fellows with a pending voting duty.
    It must be called by an Editorial Administrator.

    If `rec_id` is given, then only email Fellows voting on this particular rec.
    """
    recommendation = get_object_or_404(EICRecommendation, pk=rec_id)

    fellows = []
    for fellow in recommendation.eligible_to_vote.all():
        if (
            fellow not in recommendation.voted_for.all()
            and fellow not in recommendation.voted_against.all()
            and fellow not in recommendation.voted_abstain.all()
            and fellow not in fellows
        ):
            fellows.append(fellow)
            SubmissionUtils.load(
                {
                    "fellow": fellow,
                    "recommendation": recommendation,
                }
            )
            SubmissionUtils.send_fellow_voting_reminder_email()

    ack_message = "Email reminders have been sent to: <ul>"
    for name in sorted(map(lambda f: f.user.get_full_name(), fellows)):
        ack_message += "<li>" + name + "</li>"
    ack_message += "</ul>"
    context = {
        "ack_message": Template(ack_message).render(Context({})),
        "followup_message": "Return to the ",
        "followup_link": reverse("submissions:pool:pool"),
        "followup_link_label": "Submissions pool",
    }
    return render(request, "scipost/acknowledgement.html", context)


@login_required
@user_passes_test(is_edadmin_or_senior_fellow)
def editor_invitations(request, identifier_w_vn_nr):
    """
    Update/show invitations of editors for Submission.
    """
    submission = get_object_or_404(
        Submission.objects.without_eic(),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    assignments = submission.editorial_assignments.order_by("invitation_order")
    context = {
        "submission": submission,
        "assignments": assignments,
    }

    if submission.editor_in_charge:
        # Show current assignment if editor is assigned.
        context["active_assignment"] = assignments.filter(
            to=submission.editor_in_charge
        )
    else:
        # Show formset if editor is not yet assigned.
        formset = PreassignEditorsFormSet(request.POST or None, submission=submission)

        if formset.is_valid():
            formset.save()
            submission.add_event_for_edadmin(
                f"{request.user.first_name} {request.user.last_name} has edited the assignments."
            )
            messages.success(request, "Editor pre-assignments saved.")
            return redirect(
                reverse(
                    "submissions:editor_invitations",
                    args=(submission.preprint.identifier_w_vn_nr,),
                )
            )
        elif request.method == "POST":
            messages.warning(request, "Invalid form. Please try again.")
        context["formset"] = formset
    return render(
        request, "submissions/admin/submission_preassign_editors.html", context
    )


@permission_required("scipost.can_assign_submissions", raise_exception=True)
def send_editorial_assignment_invitation(request, identifier_w_vn_nr, assignment_id):
    """Force-send invitation for EditorialAssignment."""
    assignment = get_object_or_404(
        EditorialAssignment.objects.preassigned(), id=assignment_id
    )
    is_sent = assignment.send_invitation()
    if is_sent:
        messages.success(request, "Invitation sent.")
    else:
        messages.warning(request, "Invitation not sent.")
    return redirect(
        reverse(
            "submissions:editor_invitations",
            args=(assignment.submission.preprint.identifier_w_vn_nr,),
        )
    )


class SubmissionReassignmentView(
    SuccessMessageMixin, SubmissionAdminViewMixin, UpdateView
):
    """Assign new EIC to Submission."""

    permission_required = "scipost.can_reassign_submissions"  # TODO: New permission
    queryset = Submission.objects.assigned()
    template_name = "submissions/admin/submission_reassign.html"
    form_class = SubmissionReassignmentForm
    editorial_page = False
    success_url = reverse_lazy("submissions:pool:pool")
    success_message = "Editor successfully replaced."


@permission_required("scipost.can_fix_College_decision")
def _hx_submission_update_target_journal(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    return render(
        request,
        "submissions/admin/_submission_update_target_journal.html",
        context={
            "submission": submission,
        },
    )


@permission_required("scipost.can_fix_College_decision")
def _hx_submission_update_target_journal_form(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    target_old = submission.submitted_to.name
    form = SubmissionTargetJournalForm(request.POST or None, instance=submission)
    context = {
        "submission": submission,
    }
    if form.is_valid():
        form.save()
        if form.has_changed():
            submission.add_general_event(
                "The target Journal has been changed from %s to %s"
                % (target_old, submission.submitted_to.name)
            )
        return render(
            request,
            "submissions/admin/_submission_update_target_journal.html",
            context,
        )
    context["form"] = form
    return render(
        request,
        "submissions/admin/_hx_submission_update_target_journal_form.html",
        context,
    )


@permission_required("scipost.can_fix_College_decision")
def _hx_submission_update_target_proceedings(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    return render(
        request,
        "submissions/admin/_submission_update_target_proceedings.html",
        context={
            "submission": submission,
        },
    )


@permission_required("scipost.can_fix_College_decision")
def _hx_submission_update_target_proceedings_form(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    target_old = str(submission.proceedings)
    form = SubmissionTargetProceedingsForm(request.POST or None, instance=submission)
    context = {
        "submission": submission,
    }
    if form.is_valid():
        form.save()
        if form.has_changed():
            submission.add_general_event(
                "The target Proceedings has been changed from %s to %s"
                % (target_old, str(submission.proceedings))
            )
        return render(
            request,
            "submissions/admin/_submission_update_target_proceedings.html",
            context,
        )
    context["form"] = form
    return render(
        request,
        "submissions/admin/_hx_submission_update_target_proceedings_form.html",
        context,
    )


@permission_required("scipost.can_fix_College_decision")
def _hx_submission_update_collections(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    return render(
        request,
        "submissions/admin/_submission_update_collections.html",
        context={
            "submission": submission,
        },
    )


@permission_required("scipost.can_fix_College_decision")
def _hx_submission_update_collections_form(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    target_old = ", ".join([str(c) for c in submission.collections.all()])
    form = SubmissionCollectionsForm(request.POST or None, instance=submission)
    context = {
        "submission": submission,
    }
    if form.is_valid():
        form.save()
        if form.has_changed():
            submission.add_general_event(
                "The Collections have been changed from %s to %s"
                % (target_old, str(submission.proceedings))
            )
        return render(
            request,
            "submissions/admin/_submission_update_collections.html",
            context,
        )
    context["form"] = form
    return render(
        request,
        "submissions/admin/_hx_submission_update_collections_form.html",
        context,
    )


@permission_required("scipost.can_fix_College_decision")
def _hx_submission_update_preprint_file(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    return render(
        request,
        "submissions/admin/_submission_update_preprint_file.html",
        context={
            "submission": submission,
        },
    )


@permission_required("scipost.can_fix_College_decision")
def _hx_submission_update_preprint_file_form(request, identifier_w_vn_nr):
    preprint = get_object_or_404(Preprint, identifier_w_vn_nr=identifier_w_vn_nr)
    filedata_old = (
        f"{preprint._file.name.rpartition('/')[2]} ({preprint._file.size // 1024} kb)"
    )
    context = {
        "submission": preprint.submission,
    }
    if request.method == "POST":
        form = SubmissionPreprintFileForm(
            request.POST, request.FILES, instance=preprint
        )
        if form.is_valid():
            form.save()
            if form.has_changed():
                preprint.submission.add_general_event(
                    f"The preprint file has been changed from "
                    f"{filedata_old} to "
                    f"{preprint._file.name.rpartition('/')[2]} "
                    f"({preprint._file.size // 1024} kb)"
                )
            return render(
                request,
                "submissions/admin/_submission_update_preprint_file.html",
                context,
            )
    else:
        form = SubmissionPreprintFileForm(instance=preprint)
    context["form"] = form
    return render(
        request,
        "submissions/admin/_hx_submission_update_preprint_file_form.html",
        context,
    )


def _hx_submission_add_specialty(request, identifier_w_vn_nr):
    """
    Renders the form to add a specialty to a submission. Returns the ontological info table if successful.
    """
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )

    # User should have access only if:
    # - they are EdAdmin
    # - they are EIC of the submission if one is assigned
    # - they are a Fellow of the submission if no EIC is assigned
    if not (
        is_edadmin(request.user)
        or (submission.editor_in_charge is not None)
        and (submission.editor_in_charge == request.user.contributor)
        or (submission.editor_in_charge is None)
        and submission.fellows.filter(contributor=request.user.contributor).exists()
    ):
        return HTMXPermissionsDenied(
            "You are not allowed to add a specialty to this submission."
        )

    form = SpecialtyInlineForm(request.POST or None, submission=submission)
    form.helper.attrs["hx-post"] = reverse(
        "submissions:_hx_submission_add_specialty",
        kwargs={"identifier_w_vn_nr": identifier_w_vn_nr},
    )

    if form.is_valid():
        specialty = form.cleaned_data["specialty"]
        submission.specialties.add(specialty)
        submission.add_event_for_edadmin(
            f"Specialty {specialty} by {request.user.contributor.profile.full_name}."
        )
        submission.fellows.add(*submission.get_default_fellowship())

        response = TemplateResponse(
            request,
            "submissions/_submission_ontological_info_table.html",
            {"submission": submission},
        )

        response["HX-Retarget"] = f"#submission-{submission.id}-ontological-info-table"
        return response

    return TemplateResponse(request, "htmx/crispy_form.html", {"form": form})


class PreassignmentView(SubmissionAdminViewMixin, UpdateView):
    """Do preassignment of Submissions."""

    permission_required = "scipost.can_run_preassignment"
    queryset = Submission.objects.preassignment()
    template_name = "submissions/admin/submission_preassignment.html"
    form_class = SubmissionPreassignmentForm
    editorial_page = True
    success_url = reverse_lazy("submissions:pool:pool")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["current_user"] = self.request.user
        return kwargs


class SubmissionConflictsView(SubmissionAdminViewMixin, DetailView):
    """List all conflicts for a certain Submission."""

    permission_required = "scipost.can_run_preassignment"
    template_name = "submissions/admin/submission_conflicts.html"
    editorial_page = True
    success_url = reverse_lazy("submissions:pool:pool")

    def get_object(self) -> Submission:
        obj: Submission = super().get_object()

        obj.fellows_with_conflicts = obj.fellows.all().prefetch_related(
            *obj.get_coi_prefetches_for_profile_path("contributor__profile")
        )

        return obj


class EICRecommendationDetailView(
    SubmissionMixin, LoginRequiredMixin, UserPassesTestMixin, DetailView
):
    """
    EICRecommendation detail, visible to EdAdmin.
    """

    model = EICRecommendation
    template_name = "submissions/pool/recommendation.html"
    context_object_name = "recommendation"

    def test_func(self):
        """Grants access to EdAdmin."""
        if self.request.user.has_perm("scipost.can_fix_College_decision"):
            return True
        submission = get_object_or_404(
            Submission,
            preprint__identifier_w_vn_nr=self.kwargs.get("identifier_w_vn_nr"),
        )
        eicrec = submission.eicrecommendations.last()
        if eicrec.eligible_to_vote.filter(dbuser=self.request.user).exists():
            return True
        return False

    def get_object(self):
        """Return the latest version of the EICRecommendation associated to this Submission."""
        return self.submission.eicrecommendations.last()


@login_required
@fellowship_or_admin_required()
@transaction.atomic
def _hx_recommendation_vote_form(request, rec_id):
    """Form view for Fellows to cast their vote on EICRecommendation."""
    submissions = Submission.objects.in_pool(request.user)
    previous_vote = None
    try:
        recommendation = EICRecommendation.objects.user_must_vote_on(request.user).get(
            submission__in=submissions, id=rec_id
        )
        initial = {"vote": "abstain"}
    except EICRecommendation.DoesNotExist:  # Try to find an EICRec already voted on:
        try:
            recommendation = EICRecommendation.objects.user_current_voted(
                request.user
            ).get(submission__in=submissions, id=rec_id)
            if request.user.contributor in recommendation.voted_for.all():
                previous_vote = "agree"
            elif request.user.contributor in recommendation.voted_against.all():
                previous_vote = "disagree"
            elif request.user.contributor in recommendation.voted_abstain.all():
                previous_vote = "abstain"
        except EICRecommendation.DoesNotExist:
            return HTMXPermissionsDenied(
                "You are not allowed to vote on this recommendation."
            )
    initial = {"vote": previous_vote}

    if request.POST:
        form = RecommendationVoteForm(request.POST, recommendation=recommendation)
    else:
        form = RecommendationVoteForm(initial=initial, recommendation=recommendation)
    if form.is_valid():
        # Delete previous tierings and alternative recs, irrespective of the vote
        SubmissionTiering.objects.filter(
            submission=recommendation.submission, fellow=request.user.contributor
        ).delete()
        AlternativeRecommendation.objects.filter(
            eicrec=recommendation, fellow=request.user.contributor
        ).delete()
        if form.cleaned_data["vote"] == "agree":
            try:
                recommendation.voted_for.add(request.user.contributor)
            except IntegrityError:
                messages.warning(
                    request, "You have already voted for this Recommendation."
                )
            recommendation.voted_against.remove(request.user.contributor)
            recommendation.voted_abstain.remove(request.user.contributor)
            # Add a tiering if form filled in:
            if (
                recommendation.recommendation == EIC_REC_PUBLISH
                and form.cleaned_data["tier"] != ""
            ):
                tiering = SubmissionTiering(
                    submission=recommendation.submission,
                    fellow=request.user.contributor,
                    for_journal=recommendation.for_journal,
                    tier=form.cleaned_data["tier"],
                )
                tiering.save()
        elif form.cleaned_data["vote"] == "disagree":
            recommendation.voted_for.remove(request.user.contributor)
            try:
                recommendation.voted_against.add(request.user.contributor)
            except IntegrityError:
                messages.warning(
                    request, "You have already voted against this Recommendation."
                )
            recommendation.voted_abstain.remove(request.user.contributor)
            # Create an alternative recommendation, if given
            if (
                form.cleaned_data["alternative_for_journal"]
                and form.cleaned_data["alternative_recommendation"]
            ):
                altrec = AlternativeRecommendation(
                    eicrec=recommendation,
                    fellow=request.user.contributor,
                    for_journal=form.cleaned_data["alternative_for_journal"],
                    recommendation=form.cleaned_data["alternative_recommendation"],
                )
                altrec.save()
        elif form.cleaned_data["vote"] == "abstain":
            recommendation.voted_for.remove(request.user.contributor)
            recommendation.voted_against.remove(request.user.contributor)
            try:
                recommendation.voted_abstain.add(request.user.contributor)
            except IntegrityError:
                messages.warning(
                    request, "You have already abstained on this Recommendation."
                )
                pass
        votechanged = previous_vote and form.cleaned_data["vote"] != previous_vote
        if votechanged:
            remark = Remark(
                contributor=request.user.contributor,
                recommendation=recommendation,
                date=timezone.now(),
                remark="Note from EdAdmin: {full_name} changed vote from {previous} to {current}".format(
                    full_name=request.user.get_full_name(),
                    previous=previous_vote,
                    current=form.cleaned_data["vote"],
                ),
            )
            remark.save()
        recommendation.save()
        messages.success(request, "Thank you for your vote.")

    context = {
        "recommendation": recommendation,
        "form": form,
        "previous_vote": previous_vote,
    }
    return TemplateResponse(
        request, "submissions/pool/_hx_recommendation_vote_form.html", context
    )


class EditorialDecisionCreateView(SubmissionMixin, PermissionsMixin, CreateView):
    """For EdAdmin to create the editorial decision on a Submission, after voting is completed.

    The complete workflow involves drafting the decision with this view,
    possibly updating it with EditorialDecisionUpdateView, and (when all details
    are correct) finally posting to the ``fix_editorial_decision`` view.
    """

    permission_required = "scipost.can_fix_College_decision"
    model = EditorialDecision
    form_class = EditorialDecisionForm
    template_name = "submissions/admin/editorial_decision_form.html"

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        eicrec = self.submission.eicrecommendations.last()
        for_journal = eicrec.for_journal
        decision = (
            eicrec.recommendation
            if eicrec.recommendation in [EIC_REC_PUBLISH, EIC_REC_REJECT]
            else EIC_REC_PUBLISH
        )
        status = EditorialDecision.DRAFTED
        initial.update(
            {
                "submission": self.submission.id,
                "for_journal": for_journal,
                "decision": decision,
                "status": status,
            }
        )
        return initial


class EditorialDecisionDetailView(SubmissionMixin, PermissionsMixin, DetailView):
    permission_required = "scipost.can_fix_College_decision"
    model = EditorialDecision
    context_object_name = "decision"
    template_name = "submissions/admin/editorial_decision_detail.html"

    def get_object(self):
        try:
            return self.submission.editorial_decision
        except EditorialDecision.DoesNotExist:
            return render(
                self.request,
                "scipost/error.html",
                {
                    "errormessage",
                    "No editorial decision has yet been taken on this Submission.",
                },
            )


class EditorialDecisionUpdateView(SubmissionMixin, PermissionsMixin, UpdateView):
    permission_required = "scipost.can_fix_College_decision"
    model = EditorialDecision
    context_object_name = "decision"
    form_class = EditorialDecisionForm
    template_name = "submissions/admin/editorial_decision_form.html"

    def get_object(self):
        try:
            return self.submission.editorial_decision
        except EditorialDecision.DoesNotExist:
            return render(
                self.request,
                "scipost/error.html",
                {
                    "errormessage",
                    "No editorial decision has yet been taken on this Submission.",
                },
            )


@login_required
@permission_required("scipost.can_fix_College_decision")
def fix_editorial_decision(request, identifier_w_vn_nr):
    """Fix the editorial decision, which is then final. Email authors.

    This is the method completing the editorial decision process.
    It follows the creation/updating of the decision using
    EditorialDecisionCreateView and EditorialDecisionUpdateView.
    """

    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    decision = submission.editorial_decision
    # Set latest EICRecommedation to DECISION_FIXED
    eicrec = submission.eicrecommendations.last()
    eicrec.status = DECISION_FIXED
    eicrec.save()

    if decision.decision == EIC_REC_PUBLISH:
        new_sub_status = submission.ACCEPTED_IN_TARGET
        if (
            decision.for_journal != submission.submitted_to
            # promotion to Selections assumed automatically accepted by authors:
            and decision.for_journal.name != "SciPost Selections"
        ):
            new_sub_status = (
                submission.ACCEPTED_IN_ALTERNATIVE_AWAITING_PUBOFFER_ACCEPTANCE
            )
        Submission.objects.filter(id=submission.id).update(
            visible_public=True,
            status=new_sub_status,
            acceptance_date=datetime.date.today(),
            latest_activity=timezone.now(),
        )

        # Start a new ProductionStream
        get_or_create_production_stream(submission)

    elif decision.decision == EIC_REC_REJECT:
        # Decision: Rejection. Auto hide from public and Pool.
        Submission.objects.filter(id=submission.id).update(
            visible_public=False,
            visible_pool=False,
            status=Submission.REJECTED,
            latest_activity=timezone.now(),
        )
        submission.get_other_versions().update(visible_public=False)

    # Force-close the refereeing round for new referees.
    Submission.objects.filter(id=submission.id).update(
        open_for_reporting=False, open_for_commenting=False
    )

    # Cancel outstanding refereeing invitations
    for invitation in submission.referee_invitations.outstanding():
        SubmissionUtils.load({"invitation": invitation})
        if invitation.date_invited is not None:
            SubmissionUtils.send_ref_cancellation_email()
        invitation.cancelled = True
        invitation.save()

    # Update Editorial Assignment statuses.
    EditorialAssignment.objects.filter(
        submission=submission, to=submission.editor_in_charge
    ).update(status=EditorialAssignment.STATUS_COMPLETED)

    mail_request = MailEditorSubview(
        request,
        mail_code="authors/inform_authors_editorial_decision",
        decision=decision,
    )

    if mail_request.is_valid():
        messages.success(request, "Authors have been emailed about the decision")
        mail_request.send_mail()
        if (
            decision.decision == EIC_REC_REJECT
            or decision.for_journal.name == "SciPost Selections"
            or decision.for_journal == submission.submitted_to
        ):
            decision.status = EditorialDecision.FIXED_AND_ACCEPTED
        else:  # paper is accepted, but in subsidiary journal
            decision.status = EditorialDecision.AWAITING_PUBOFFER_ACCEPTANCE
        decision.save()
        submission.add_general_event(
            "The Editorial Decision has been fixed for Journal %s: %s (with status: %s)."
            % (
                str(decision.for_journal),
                decision.get_decision_display(),
                decision.get_status_display(),
            )
        )

        return redirect("submissions:pool:pool")
    else:
        return mail_request.interrupt()


@login_required
@permission_required("scipost.can_fix_College_decision")
def restart_refereeing(request, identifier_w_vn_nr):
    """Restart the latest refereeing round.

    To be invoked by EdAdmin to restart the latest refereeing round on a Submission.
    Typical circumstances where this might be invoked:

    * College vote did not converge
    * authors have appealed a decision to publish as Core (if they had submitted to flagship)
    """
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )

    form = RestartRefereeingForm(request.POST or None, submission=submission)
    if form.is_valid():
        if form.is_confirmed():
            submission = form.save()
            submission.add_general_event("Refereeing has been restarted.")
            messages.success(
                request, "Refereeing has been restarted (the EIC must choose a cycle)"
            )
        else:
            messages.error(request, "Refereeing restart aborted.")
        return redirect(
            reverse(
                "submissions:editorial_page",
                args=(submission.preprint.identifier_w_vn_nr,),
            )
        )
    context = {"submission": submission, "form": form}
    return render(request, "submissions/restart_refereeing.html", context)


@login_required
def accept_puboffer(request, identifier_w_vn_nr):
    """
    Method for authors to accept an outstanding publication offer.

    A publication offer occurs when the relevant College agrees on a
    Publish recommendation for a journal which is subsidiary to the one
    originally submitted to by the authors.

    This method handles acceptance of this offer by updating the status
    of the Submission and of the EditorialDecision. It then redirects to
    the personal page.
    """

    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    errormessage = ""
    if request.user.contributor.id != submission.submitted_by.id:
        errormessage = (
            "You are not marked as the submitting author of this Submission, "
            "and thus are not allowed to take this action."
        )
    if submission.status != (
        submission.ACCEPTED_IN_ALTERNATIVE_AWAITING_PUBOFFER_ACCEPTANCE
    ):
        errormessage = (
            "This Submission's status is incompatible with accepting"
            " a publication offer."
        )
    if errormessage != "":
        return render(request, "scipost/error.html", {"errormessage": errormessage})
    Submission.objects.filter(id=submission.id).update(
        status=Submission.ACCEPTED_IN_ALTERNATIVE
    )
    EditorialDecision.objects.filter(id=submission.editorial_decision.id).update(
        status=EditorialDecision.FIXED_AND_ACCEPTED
    )
    mail_sender = DirectMailUtil(
        "authors/confirm_puboffer_acceptance", submission=submission
    )
    mail_sender.send_mail()
    submission.add_general_event("Authors have accepted the publication offer.")
    messages.success(
        request,
        (
            "Your acceptance of the publication offer has been registered. "
            "Congratulations! We will immediately start producing the proofs."
        ),
    )
    return redirect(reverse("scipost:personal_page"))


class PlagiarismView(SubmissionAdminViewMixin, UpdateView):
    """Administration detail page of Plagiarism report."""

    permission_required = "scipost.can_do_plagiarism_checks"
    template_name = "submissions/admin/iThenticate_plagiarism_report.html"
    editorial_page = True
    form_class = iThenticateReportForm

    def get_object(self):
        """Get the iThenticate_plagiarism_report as a linked object from the Submission."""
        submission = super().get_object()
        return submission.iThenticate_plagiarism_report


class PlagiarismReportPDFView(
    SubmissionAdminViewMixin, SingleObjectMixin, RedirectView
):
    """Redirect to Plagiarism report PDF at iThenticate."""

    permission_required = "scipost.can_do_plagiarism_checks"
    editorial_page = True

    # Reset queryset to all submissions (if user is edadmin)
    def get_queryset(self):
        if is_edadmin(self.request.user):
            return Submission.objects.all()
        else:
            return super().get_queryset()

    def get_redirect_url(self, *args, **kwargs):
        """Get the temporary url provided by the iThenticate API."""
        submission = self.get_object()
        if not submission.iThenticate_plagiarism_report:
            raise Http404
        url = submission.iThenticate_plagiarism_report.get_report_url()

        if not url:
            raise Http404
        return url


class PlagiarismInternalView(SubmissionAdminViewMixin, DetailView):
    """
    Check for matching title, author, abstract in Submissions and Publications.
    """

    permission_required = "scipost.can_run_preassignment"
    template_name = "submissions/admin/plagiarism_internal_check.html"
    editorial_page = True

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        submission = self.get_object()

        context["submission_matches"] = []
        if "submission_matches" in submission.internal_plagiarism_matches:
            for sub_match in submission.internal_plagiarism_matches[
                "submission_matches"
            ]:
                context["submission_matches"].append(
                    {
                        "submission": Submission.objects.get(
                            preprint__identifier_w_vn_nr=sub_match[
                                "identifier_w_vn_nr"
                            ],
                        ),
                        "ratio_title": sub_match["ratio_title"],
                        "ratio_authors": sub_match["ratio_authors"],
                        "ratio_abstract": sub_match["ratio_abstract"],
                    }
                )

        context["publication_matches"] = []
        if "publication_matches" in submission.internal_plagiarism_matches:
            for pub_match in submission.internal_plagiarism_matches[
                "publication_matches"
            ]:
                context["publication_matches"].append(
                    {
                        "publication": Publication.objects.get(
                            doi_label=pub_match["doi_label"]
                        ),
                        "ratio_title": pub_match["ratio_title"],
                        "ratio_authors": pub_match["ratio_authors"],
                        "ratio_abstract": pub_match["ratio_abstract"],
                    }
                )

        return context


##############
# Monitoring #
##############


def submissions_versus_fellows(submissions):
    stats = []
    from ontology.models import AcademicField

    for acad_field in AcademicField.objects.all():
        for specialty in acad_field.specialties.all():
            submissions_in_spec = submissions.filter(
                acad_field=acad_field, specialties__in=[specialty]
            )
            nr_streams = len(
                submissions_in_spec.filter(is_resubmission_of__isnull=True)
            )
            number = len(submissions_in_spec)
            fellows = Fellowship.objects.active().filter(
                contributor__profile__specialties__in=[specialty]
            )
            fellows_total = fellows.count()
            fellows_senior = fellows.senior().count()
            fellows_regular = fellows.regular().count()
            fellows_guest = fellows.guests().count()
            if number > 0:
                stats.append(
                    {
                        "acad_field": acad_field,
                        "specialty": specialty,
                        "nr_streams": nr_streams,
                        "number": number,
                        "fellows_total": fellows_total,
                        "fellows_senior": fellows_senior,
                        "fellows_regular": fellows_regular,
                        "fellows_guest": fellows_guest,
                        "ratio": (
                            nr_streams / fellows_total
                            if fellows_total > 0
                            else nr_streams
                        ),
                    }
                )
    return sorted(stats, key=lambda tup: tup["ratio"], reverse=True)


def submissions_processing_timescales(submissions: QuerySet[Submission], phase):
    """
    Generate a tuple containing information about timescales on submissions.

    :param phase: one of `assignment`, `acceptance`

    """
    timescales = []
    now = timezone.now()
    from ontology.models import AcademicField

    for acad_field in AcademicField.objects.all():
        for specialty in acad_field.specialties.all():
            submissions_in_spec = submissions.filter(
                acad_field=acad_field, specialties__in=[specialty]
            )
            number = len(submissions_in_spec)
            if number > 0:
                waiting_days = 0
                total_waiting_days = 0
                max_waiting_days = 0
                for sub in submissions_in_spec.all():
                    if phase == "assignment":
                        waiting_days = workdays_between(sub.submission_date, now)
                    elif (
                        phase == "original_submission_to_acceptance"
                        and sub.acceptance_date
                    ):
                        waiting_days = workdays_between(
                            sub.original_submission_date, sub.acceptance_date
                        )
                    total_waiting_days += waiting_days
                    max_waiting_days = max(waiting_days, max_waiting_days)
                timescales.append(
                    {
                        "acad_field": acad_field,
                        "specialty": specialty,
                        "number": number,
                        "waiting_days": total_waiting_days,
                        "avg_waiting_days": round(total_waiting_days / number, 2),
                        "max_waiting_days": max_waiting_days,
                    }
                )
    return sorted(timescales, key=lambda tup: tup["number"], reverse=True)


def monitor(request):
    """
    Dashboard providing an overview of the status of submission workflows.
    """
    # Compute stats for all submissions under processing
    # Exclude submissions to Proceedings
    submissions = Submission.objects.exclude(submitted_to__name__contains="Proceedings")
    context = {
        "submissions_versus_fellows": submissions_versus_fellows(
            submissions.filter(
                submission_date__gt=timezone.now() - datetime.timedelta(days=365),
            )
        ),
        "timescales_assignment": submissions_processing_timescales(
            submissions.seeking_assignment(), "assignment"
        ),
        "timescales_original_submission_to_acceptance": submissions_processing_timescales(
            submissions.accepted(), "original_submission_to_acceptance"
        ),
    }
    return render(request, "submissions/monitor.html", context)


class HXRefereeIndicationFormSetView(HXFormSetView):
    form_class = RefereeIndicationForm

    def formset_valid(self):
        response = HTMXResponse("Referee indications saved successfully", tag="success")
        response.headers["HX-Trigger"] = "referee-indications-updated"
        return response

    def get_factory_kwargs(self):
        #! Improvement: Kind of a hacky way to reuse the same decorator code
        def save_profile(request, **kwargs):
            # Create a dummy view that saves the profile kwarg on self
            setattr(kwargs.pop("self"), "profile", kwargs.pop("profile"))

        resolve_profile(save_profile)(self.request, self=self)

        identifier_w_vn_nr = self.kwargs.get("identifier_w_vn_nr")
        self.submission = Submission.objects.get(
            preprint__identifier_w_vn_nr=identifier_w_vn_nr
        )

        kwargs = super().get_factory_kwargs()
        kwargs.update({"can_delete": True})

        return kwargs

    def get_formset_kwargs(self):
        kwargs = super().get_formset_kwargs()

        kwargs.update(
            {
                "queryset": RefereeIndication.objects.all()
                .for_submission(self.submission)
                .by_profile(self.profile),
            }
        )

        return kwargs

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        kwargs.update({"submission": self.submission, "profile": self.profile})

        return kwargs


@resolve_profile
def referee_indications(request, identifier_w_vn_nr, profile=None):
    """
    View to display the referee indications table for a submission,
    the creation formset, and the instruction set for either.
    """

    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )

    if profile is None:
        raise PermissionDenied("You must be logged in to view this page.")

    context = {
        "submission": submission,
        "referee_indications": RefereeIndication.objects.all()
        .for_submission(submission)
        .visible_by(profile),
    }

    return render(request, "submissions/referee_indications.html", context)


@resolve_profile
def _hx_referee_indication_table(request, identifier_w_vn_nr, profile=None):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )

    if profile is None:
        raise PermissionDenied("You must be logged in to view this page.")

    referee_indications = (
        RefereeIndication.objects.all()
        .for_submission(submission)
        .visible_by(profile)
        .order_by("-indication", "indicated_by", "referee__last_name", "last_name")
    )

    #! Refactor: This is a bit of a hack to avoid having to add a new permission
    try:
        is_in_fellow_pool = profile.contributor.id in submission.fellows.values_list(
            "contributor__id", flat=True
        )
        is_submission_eic = submission.editor_in_charge == profile.contributor
    except Profile.contributor.RelatedObjectDoesNotExist:
        is_in_fellow_pool = False
        is_submission_eic = False
    can_view_indicated_by_names = is_submission_eic or not is_in_fellow_pool

    return render(
        request,
        "submissions/_hx_referee_indication_table.html",
        {
            "submission": submission,
            "profile": profile,
            "referee_indications": referee_indications,
            "can_view_indicated_by_names": can_view_indicated_by_names,
        },
    )


@resolve_profile
def _hx_referee_indication_delete(request: HttpRequest, pk, profile=None):
    # Guard against invalid request methods
    if request.method != "DELETE":
        return HTMXResponse("Invalid request method", tag="danger")

    referee_indication = get_object_or_404(RefereeIndication, pk=pk)

    is_author = profile == referee_indication.indicated_by
    if not is_author:
        return HTMXResponse("You are not allowed to delete this referee indication")

    referee_indication.delete()
    return empty(request)
