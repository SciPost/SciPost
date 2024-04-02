__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import urllib

from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User, Group
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetView,
    PasswordResetConfirmView,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.core.paginator import Paginator
from django.urls import reverse, reverse_lazy
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template import Context, Template
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic.edit import DeleteView, CreateView
from django.views.generic.list import ListView
from django.views.static import serve

from dal import autocomplete
from guardian.decorators import permission_required
from scipost.permissions import permission_required_htmx, HTMXResponse

from .constants import SciPost_from_addresses_dict, NORMAL_CONTRIBUTOR
from .decorators import has_contributor, is_contributor_user
from .models import Contributor, UnavailabilityPeriod, AuthorshipClaim
from .forms import (
    SciPostAuthenticationForm,
    UserAuthInfoForm,
    TOTPDeviceForm,
    UnavailabilityPeriodForm,
    RegistrationForm,
    AuthorshipClaimForm,
    VetRegistrationForm,
    reg_ref_dict,
    UpdatePersonalDataForm,
    UpdateUserDataForm,
    ContributorMergeForm,
    EmailGroupMembersForm,
    EmailParticularForm,
    SendPrecookedEmailForm,
)
from .mixins import PermissionsMixin, PaginationMixin
from .utils import EMAIL_FOOTER, SCIPOST_SUMMARY_FOOTER, SCIPOST_SUMMARY_FOOTER_HTML

from blog.models import BlogPost
from colleges.permissions import (
    fellowship_or_admin_required,
    is_edadmin_or_active_fellow,
)
from commentaries.models import Commentary
from commentaries.forms import CommentarySearchForm
from comments.models import Comment
from comments.forms import CommentSearchForm
from common.utils import get_current_domain
from invitations.constants import STATUS_REGISTERED
from invitations.models import RegistrationInvitation
from journals.models import Journal, Publication, PublicationAuthorsTable
from journals.forms import PublicationSearchForm
from mails.utils import DirectMailUtil
from news.models import NewsItem
from organizations.decorators import has_contact
from organizations.models import Organization, Contact
from organizations.forms import UpdateContactDataForm
from profiles.models import Profile
from submissions.models import (
    Submission,
    RefereeInvitation,
    Report,
    EditorialAssignment,
    EICRecommendation,
)
from submissions.forms import PortalSubmissionSearchForm, ReportSearchForm
from theses.models import ThesisLink
from theses.forms import ThesisSearchForm


###########
# Sitemap #
###########


def sitemap_xml(request):
    """
    Dynamically generate a sitemap (xml) for search engines.
    """
    newsitems = NewsItem.objects.homepage()
    journals = Journal.objects.active()
    contributors = Contributor.objects.active()
    submissions = Submission.objects.public()
    publications = Publication.objects.published().order_by("-publication_date")
    commentaries = Commentary.objects.vetted()
    theses = ThesisLink.objects.vetted()
    organizations = Organization.objects.all()
    context = {
        "newsitems": newsitems,
        "journals": journals,
        "contributors": contributors,
        "submissions": submissions,
        "publications": publications,
        "commentaries": commentaries,
        "theses": theses,
        "organizations": organizations,
    }
    return render(request, "scipost/sitemap.xml", context)


################
# Autocomplete #
################


class GroupAutocompleteView(autocomplete.Select2QuerySetView):
    """
    View to feed the Select2 widget.
    """

    def get_queryset(self):
        if not self.request.user.has_perm("auth.view_group"):
            return Group.objects.none()
        qs = Group.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs


class UserAutocompleteView(autocomplete.Select2QuerySetView):
    """
    View to feed the Select2 widget.
    """

    def get_queryset(self):
        if not self.request.user.has_perm("auth.view_user"):
            return None
        qs = User.objects.all()
        if self.q:
            qs = qs.filter(
                Q(username__icontains=self.q)
                | Q(email__icontains=self.q)
                | Q(first_name__icontains=self.q)
                | Q(last_name__icontains=self.q)
            )
        return qs

    def get_result_label(self, item):
        return f"{item.last_name}, {item.first_name}"


##############
# Utilitites #
##############


@staff_member_required
def trigger_error(request):
    division_by_zero = 1 / 0


def _hx_messages(request):
    return render(request, "scipost/_hx_messages.html")


#############
# Main view
#############


def portal(request):
    if request.GET.get("field", None):
        if request.GET["field"] != request.session["session_acad_field_slug"]:
            request.session["session_specialty_slug"] = ""
        request.session["session_acad_field_slug"] = request.GET["field"]
    context = {"load_header_forms": request.GET.get("tab", None) != None}
    return render(request, "scipost/portal/portal.html", context)


def portal_hx_home(request):
    """Homepage view of SciPost."""
    if NewsItem.objects.homepage().exists():
        news_items = NewsItem.objects.homepage().order_by("-date")[:3]
    else:
        news_items = NewsItem.objects.none()
    latest_blogpost = BlogPost.objects.published().first()
    context = {
        "news_items": news_items,
        "latest_blogpost": latest_blogpost,
        "publications": Publication.objects.published()
        .exclude(doi_label__contains="Proc")
        .order_by("-publication_date", "-paper_nr")
        .prefetch_related("in_issue__in_journal", "specialties", "collections__series")[
            :5
        ],
    }
    return render(request, "scipost/portal/_hx_home.html", context)


@login_required
@user_passes_test(is_edadmin_or_active_fellow)
def portal_hx_tasklist(request):
    """Displays list of tasks for Fellows."""
    context = {
        "assignments_to_consider": EditorialAssignment.objects.invited().filter(
            to=request.user.contributor
        ),
        "assignments_ongoing": request.user.contributor.editorial_assignments.ongoing(),
        "recs_to_vote_on": EICRecommendation.objects.user_must_vote_on(request.user),
        "recs_current_voted": EICRecommendation.objects.user_current_voted(
            request.user
        ),
    }
    return render(request, "scipost/portal/_hx_tasklist.html", context)


def portal_hx_journals(request):
    session_acad_field_slug = request.session.get("session_acad_field_slug", None)
    journals = Journal.objects.active().select_related("college__acad_field__branch")
    context = {}
    if session_acad_field_slug and session_acad_field_slug != "all":
        journals = journals.filter(
            college__acad_field__slug=session_acad_field_slug,
        ).prefetch_related("contained_series")
        context["journals"] = journals
    else:  # build a dictionary of journals per branch / acad_field
        journals_dict = {}
        for journal in journals.all():
            branch_name = journal.college.acad_field.branch.name
            acad_field_name = journal.college.acad_field.name
            if branch_name not in journals_dict:
                journals_dict[branch_name] = {}
            if acad_field_name not in journals_dict[branch_name]:
                journals_dict[branch_name][acad_field_name] = []
            journals_dict[branch_name][acad_field_name].append(journal)
        context["journals_dict"] = journals_dict
    return render(request, "scipost/portal/_hx_journals.html", context)


def portal_hx_publications(request):
    form = PublicationSearchForm(
        acad_field_slug=request.session.get("session_acad_field_slug", None),
        specialty_slug=request.session.get("session_specialty_slug", None),
    )
    context = {"publications_search_form": form}
    return render(request, "scipost/portal/_hx_publications.html", context)


def portal_hx_publications_page(request):
    session_acad_field_slug = request.session.get("session_acad_field_slug", None)
    session_specialty_slug = request.session.get("session_specialty_slug", None)
    form = PublicationSearchForm(
        request.POST or None,
        acad_field_slug=session_acad_field_slug,
        specialty_slug=session_specialty_slug,
    )
    if form.is_valid():
        publications = form.search_results()
    else:
        publications = Publication.objects.published()
        if session_acad_field_slug and session_acad_field_slug != "all":
            publications = publications.filter(acad_field__slug=session_acad_field_slug)
            if session_specialty_slug:
                publications = publications.filter(
                    specialties__slug=session_specialty_slug
                )
    publications = publications.select_related("acad_field").prefetch_related(
        "in_journal",
        "in_issue__in_journal",
        "in_issue__in_volume__in_journal",
        "specialties",
        "collections__series",
    )
    paginator = Paginator(publications, 10)
    page_nr = request.GET.get("page")
    page_obj = paginator.get_page(page_nr)
    context = {"page_obj": page_obj}
    return render(request, "scipost/portal/_hx_publications_page.html", context)


def portal_hx_submissions(request):
    reports_needed = request.GET.get("reports_needed", False)
    form = PortalSubmissionSearchForm(
        acad_field_slug=request.session.get("session_acad_field_slug", None),
        specialty_slug=request.session.get("session_specialty_slug", None),
        reports_needed=reports_needed,
    )
    context = {"submissions_search_form": form, "reports_needed": reports_needed}
    return render(request, "scipost/portal/_hx_submissions.html", context)


def portal_hx_submissions_page(request):
    session_acad_field_slug = request.session.get("session_acad_field_slug", None)
    session_specialty_slug = request.session.get("session_specialty_slug", None)
    reports_needed = request.GET.get("reports_needed", False)
    form = PortalSubmissionSearchForm(
        request.POST or None,
        acad_field_slug=session_acad_field_slug,
        specialty_slug=session_specialty_slug,
        reports_needed=reports_needed,
    )
    if form.is_valid():
        submissions = form.search_results()
    else:
        submissions = Submission.objects.public()
        if session_acad_field_slug and session_acad_field_slug != "all":
            submissions = submissions.filter(acad_field__slug=session_acad_field_slug)
            if session_specialty_slug:
                submissions = submissions.filter(
                    specialties__slug=session_specialty_slug
                )
    submissions = submissions.select_related(
        "preprint",
        "acad_field",
        "submitted_to",
    ).prefetch_related(
        "specialties",
        "publications",
    )
    paginator = Paginator(submissions, 10)
    page_nr = request.GET.get("page")
    page_obj = paginator.get_page(page_nr)
    context = {"page_obj": page_obj, "reports_needed": reports_needed}
    return render(request, "scipost/portal/_hx_submissions_page.html", context)


def portal_hx_reports(request):
    form = ReportSearchForm(
        acad_field_slug=request.session.get("session_acad_field_slug", None),
        specialty_slug=request.session.get("session_specialty_slug", None),
    )
    context = {"reports_search_form": form}
    return render(request, "scipost/portal/_hx_reports.html", context)


def portal_hx_reports_page(request):
    session_acad_field_slug = request.session.get("session_acad_field_slug", None)
    session_specialty_slug = request.session.get("session_specialty_slug", None)
    form = ReportSearchForm(
        request.POST or None,
        acad_field_slug=session_acad_field_slug,
        specialty_slug=session_specialty_slug,
    )
    if form.is_valid():
        reports = form.search_results()
    else:
        reports = Report.objects.accepted()
    if session_acad_field_slug and session_acad_field_slug != "all":
        reports = reports.filter(submission__acad_field__slug=session_acad_field_slug)
        if session_specialty_slug and session_specialty_slug != "all":
            reports = reports.filter(
                submission__specialties__slug=session_specialty_slug
            )
    paginator = Paginator(reports, 10)
    page_nr = request.GET.get("page")
    page_obj = paginator.get_page(page_nr)
    context = {"page_obj": page_obj}
    return render(request, "scipost/portal/_hx_reports_page.html", context)


def portal_hx_comments(request):
    form = CommentSearchForm(
        acad_field_slug=request.session.get("session_acad_field_slug", None),
        specialty_slug=request.session.get("session_specialty_slug", None),
    )
    context = {"comments_search_form": form}
    return render(request, "scipost/portal/_hx_comments.html", context)


def portal_hx_comments_page(request):
    session_acad_field_slug = request.session.get("session_acad_field_slug", None)
    session_specialty_slug = request.session.get("session_specialty_slug", None)
    form = CommentSearchForm(
        request.POST or None,
        acad_field_slug=session_acad_field_slug,
        specialty_slug=session_specialty_slug,
    )
    if form.is_valid():
        comments = form.search_results()
    else:
        comments = Comment.objects.vetted()
    if session_acad_field_slug and session_acad_field_slug != "all":
        comments = comments.filter(
            Q(submissions__acad_field__slug=session_acad_field_slug)
            | Q(reports__submission__acad_field__slug=session_acad_field_slug)
            | Q(commentaries__acad_field__slug=session_acad_field_slug)
        )
        if session_specialty_slug and session_specialty_slug != "all":
            comments = comments.filter(
                Q(submissions__specialties__slug=session_specialty_slug)
                | Q(reports__submission__specialties__slug=session_specialty_slug)
                | Q(commentaries__specialties__slug=session_specialty_slug)
            )
    paginator = Paginator(comments.distinct(), 10)
    page_nr = request.GET.get("page")
    page_obj = paginator.get_page(page_nr)
    context = {"page_obj": page_obj}
    return render(request, "scipost/portal/_hx_comments_page.html", context)


def portal_hx_commentaries(request):
    form = CommentarySearchForm(
        acad_field_slug=request.session.get("session_acad_field_slug", None),
        specialty_slug=request.session.get("session_specialty_slug", None),
    )
    context = {"commentaries_search_form": form}
    return render(request, "scipost/portal/_hx_commentaries.html", context)


def portal_hx_commentaries_page(request):
    session_acad_field_slug = request.session.get("session_acad_field_slug", None)
    session_specialty_slug = request.session.get("session_specialty_slug", None)
    form = CommentarySearchForm(
        request.POST or None,
        acad_field_slug=session_acad_field_slug,
        specialty_slug=session_specialty_slug,
    )
    form.is_valid()  # trigger validation to get filtering
    commentaries = form.search_results()
    paginator = Paginator(commentaries, 10)
    page_nr = request.GET.get("page")
    page_obj = paginator.get_page(page_nr)
    context = {"page_obj": page_obj}
    return render(request, "scipost/portal/_hx_commentaries_page.html", context)


def portal_hx_theses(request):
    form = ThesisSearchForm(
        acad_field_slug=request.session.get("session_acad_field_slug", None),
        specialty_slug=request.session.get("session_specialty_slug", None),
    )
    context = {"theses_search_form": form}
    return render(request, "scipost/portal/_hx_theses.html", context)


def portal_hx_theses_page(request):
    session_acad_field_slug = request.session.get("session_acad_field_slug", None)
    session_specialty_slug = request.session.get("session_specialty_slug", None)
    form = ThesisSearchForm(
        request.POST or None,
        acad_field_slug=session_acad_field_slug,
        specialty_slug=session_specialty_slug,
    )
    form.is_valid()  # trigger validation to get filtering
    theses = form.search_results()
    paginator = Paginator(theses, 10)
    page_nr = request.GET.get("page")
    page_obj = paginator.get_page(page_nr)
    context = {"page_obj": page_obj}
    return render(request, "scipost/portal/_hx_theses_page.html", context)


def _hx_news(request):
    if NewsItem.objects.homepage().exists():
        latest_newsitem_id = NewsItem.objects.homepage().order_by("-date").first().id
        news = (
            NewsItem.objects.homepage()
            .exclude(pk=latest_newsitem_id)
            .order_by("?")
            .first()
        )
    else:
        news = NewsItem.objects.none()
    context = {"news": news}
    return render(request, "scipost/_hx_news.html", context)


def _hx_sponsors(request):
    sponsor = Organization.objects.current_sponsors().order_by("?").first()
    return render(request, "scipost/_hx_sponsors.html", {"sponsor": sponsor})


def protected_serve(request, path, show_indexes=False):
    """
    Serve media files from outside the public MEDIA_ROOT folder.

    Serve files that are saved outside the default MEDIA_ROOT folder for superusers only!
    This will be useful eg. in the admin pages.
    """
    if not request.user.is_authenticated or not request.user.is_superuser:
        # Only superusers may get to see secure files without an explicit serve method!
        raise Http404
    document_root = settings.MEDIA_ROOT_SECURE
    return serve(request, path, document_root, show_indexes)


###############
# Information
###############


def feeds(request):
    """Information page for RSS and Atom feeds."""
    return render(request, "scipost/feeds.html")


################
# Contributors:
################


@transaction.atomic
def register(request):
    """
    Contributor registration form page.

    This public registration view shows and processes the form
    that will create new user account requests. After registration
    the Contributor will need to activate their account via the mail
    sent. After activation the user needs to be vetted by the SciPost
    admin.
    """
    if request.user.is_authenticated:
        return redirect(reverse("scipost:personal_page"))

    form = RegistrationForm(request.POST or None)
    if form.is_valid():
        contributor = form.create_and_save_contributor()
        mail_util = DirectMailUtil(
            "contributors/registration_received", contributor=contributor
        )
        mail_util.send_mail()

        # Disable invitations related to the new Contributor
        RegistrationInvitation.objects.declined_or_without_response().filter(
            email=form.cleaned_data["email"]
        ).update(status=STATUS_REGISTERED)

        context = {
            "ack_header": "Thanks for registering to SciPost.",
            "ack_message": (
                """
                <h3>What happens now?</h3>
                <ul>
                <li>You will receive an email with a link to verify your email address.
                You should visit this link within 48 hours.</li>
                <li>You didn't receive this email? Check your spam folder.</li>
                <li>Your credentials will thereafter be verified. If you fulfil our
                eligibility requirements, your account will be vetted through
                (you will receive confirmation by email).</li>
                <li>If vetted through, you will then be able to login and use our facilities.</li>
                </ul>
                <h4>Why is your procedure <span style="color: red;">so complicated</span>?</h4>
                <p>It is simply part of our quality assurance processes: we want to make sure
                we are dealing with qualified academics rather than random people or robots.
                </p>
                """
            ),
        }
        return render(request, "scipost/acknowledgement.html", context)
    return render(request, "scipost/register.html", {"form": form, "invited": False})


def invitation(request, key):
    """Registration Invitation reception page.

    If a scientist has recieved an invitation (RegistrationInvitation)
    they will the registration via this view which will prefill
    the default registration form from the invitation data.
    """
    invitation = get_object_or_404(RegistrationInvitation, invitation_key=key)
    if invitation.has_responded:
        errormessage = (
            "This invitation token has already been used, "
            "or this email address is already associated to a registration."
        )
    elif timezone.now() > invitation.key_expires:
        errormessage = "The invitation key has expired."
    else:
        prefilled_fields = invitation.__dict__

        profile = Profile.objects.get(pk=prefilled_fields["profile_id"])
        if profile:
            prefilled_fields["acad_field"] = profile.acad_field
            prefilled_fields["specialties"] = profile.specialties.all()

        context = {
            "invitation": invitation,
            "form": RegistrationForm(initial=prefilled_fields),
        }
        return render(request, "scipost/register.html", context)
    return render(
        request, "scipost/accept_invitation_error.html", {"errormessage": errormessage}
    )


def activation(request, contributor_id, key):
    """
    After registration, an email verification link is sent.
    Once clicked, the account is activated.
    """
    contributor = get_object_or_404(Contributor, id=contributor_id, activation_key=key)
    if not contributor.user.is_active:
        if timezone.now() > contributor.key_expires:
            return redirect(
                reverse(
                    "scipost:request_new_activation_link",
                    kwargs={"contributor_id": contributor_id, "key": key},
                )
            )
        contributor.user.is_active = True
        contributor.user.save()
        context = {
            "ack_header": "Many thanks for confirming your email address.",
            "ack_message": (
                "Your SciPost account will soon be vetted by "
                "an administrator, after which you will be able to log in. "
                "You will soon receive an email confirmation from us!"
            ),
        }
        return render(request, "scipost/acknowledgement.html", context)
    messages.success(
        request,
        (
            "<h3>Your email has already been confirmed.</h3>"
            "Please wait for vetting of your registration."
            " We shall strive to send you an update by email within 24 hours."
        ),
    )
    return redirect(reverse("scipost:index"))


def request_new_activation_link(request, contributor_id, key):
    """
    Once a user tries to activate their account using the email verification link sent
    and the key has expired, the user is redirected here to request a new token.
    """
    contributor = get_object_or_404(Contributor, id=contributor_id, activation_key=key)
    if request.GET.get("confirm", False):
        # Generate a new email activation key and link
        contributor.generate_key()
        contributor.save()

        mail_util = DirectMailUtil(
            "contributors/new_activitation_link", contributor=contributor
        )
        mail_util.send_mail()

        context = {
            "ack_header": "We have emailed you a new activation link.",
            "ack_message": (
                "Please acknowledge it within its 48 hours validity "
                "window if you want us to proceed with vetting your registration."
            ),
        }
        return render(request, "scipost/acknowledgement.html", context)
    context = {"contributor": contributor}
    return render(request, "scipost/request_new_activation_link.html", context)


def unsubscribe(request, contributor_id, key):
    """
    The link to this method is included in all email communications
    with a Contributor. The key used is the original activation key.
    At this link, the Contributor can confirm that they does not
    want to receive any non-essential email notifications from SciPost.
    """
    contributor = get_object_or_404(Contributor, id=contributor_id, activation_key=key)
    if request.GET.get("confirm", False):
        Profile.objects.filter(pk=contributor.profile.id).update(
            accepts_SciPost_emails=False
        )
        text = (
            "<h3>We have recorded your preference</h3>"
            "You will no longer receive non-essential email from SciPost."
        )
        messages.success(request, text)
        return redirect(reverse("scipost:index"))
    return render(request, "scipost/unsubscribe.html", {"contributor": contributor})


@permission_required("scipost.can_vet_registration_requests", return_403=True)
def vet_registration_requests(request):
    """List of new Registration requests to vet."""
    contributors_to_vet = Contributor.objects.awaiting_vetting().order_by("key_expires")
    form = VetRegistrationForm()
    context = {"contributors_to_vet": contributors_to_vet, "form": form}
    return render(request, "scipost/vet_registration_requests.html", context)


@permission_required("scipost.can_vet_registration_requests", return_403=True)
def vet_registration_request_ack(request, contributor_id):
    """Form view to vet new Registration requests."""
    form = VetRegistrationForm(request.POST or None)
    contributor = Contributor.objects.get(pk=contributor_id)
    if form.is_valid():
        domain = get_current_domain()
        if form.promote_to_registered_contributor():
            contributor.status = NORMAL_CONTRIBUTOR
            contributor.vetted_by = request.user.contributor
            contributor.save()
            group = Group.objects.get(name="Registered Contributors")
            contributor.user.groups.add(group)

            # Verify if there is a pending refereeing invitation using email and invitation key.
            updated_rows = (
                RefereeInvitation.objects.awaiting_response()
                .filter(referee__isnull=True, email_address=contributor.user.email)
                .update(referee=contributor)
            )
            if contributor.invitation_key:
                updated_rows += (
                    RefereeInvitation.objects.awaiting_response()
                    .filter(
                        referee__isnull=True, invitation_key=contributor.invitation_key
                    )
                    .update(referee=contributor)
                )
            pending_ref_inv_exists = updated_rows > 0

            email_text = (
                "Dear "
                + contributor.profile.get_title_display()
                + " "
                + contributor.user.last_name
                + ", \n\nYour registration to the SciPost publication portal has been accepted. "
                "You can now login at https://" + domain + " and contribute. \n\n"
            )
            if pending_ref_inv_exists:
                email_text += (
                    "Note that you have pending refereeing invitations; please navigate to "
                    "https://"
                    + domain
                    + "/submissions/accept_or_decline_ref_invitations "
                    "(login required) to accept or decline them.\n\n"
                )
            email_text += "Thank you very much in advance, \nThe SciPost Team."
            emailmessage = EmailMessage(
                "SciPost registration accepted",
                email_text,
                "SciPost registration <registration@%s>" % domain,
                [contributor.user.email],
                bcc=["registration@%s" % domain],
                reply_to=["registration@%s" % domain],
            )
            emailmessage.send(fail_silently=False)
        else:
            ref_reason = form.cleaned_data["refusal_reason"]
            email_text = (
                "Dear "
                + contributor.profile.get_title_display()
                + " "
                + contributor.user.last_name
                + ", \n\nYour registration to the SciPost publication portal has been turned down,"
                " the reason being: "
                + reg_ref_dict[ref_reason]
                + ". You can however still view "
                "all SciPost contents, just not submit papers, comments or votes. We nonetheless "
                "thank you for your interest.\n\nThe SciPost Team."
            )
            if form.cleaned_data["email_response_field"]:
                email_text += (
                    "\n\nFurther explanations: "
                    + form.cleaned_data["email_response_field"]
                )
            emailmessage = EmailMessage(
                "SciPost registration: unsuccessful",
                email_text,
                "SciPost registration <registration@%s>" % domain,
                [contributor.user.email],
                bcc=["registration@%s" % domain],
                reply_to=["registration@%s" % domain],
            )
            emailmessage.send(fail_silently=False)
            contributor.status = form.cleaned_data["refusal_reason"]
            contributor.save()

    messages.success(request, "SciPost Registration request vetted.")
    return redirect(reverse("scipost:vet_registration_requests"))


@permission_required("scipost.can_resend_registration_requests", return_403=True)
def registration_requests(request):
    """
    List all inactive users. These are users that have filled the registration form,
    but did not yet activate their account using the validation email.
    """
    inactive_contributors = (
        Contributor.objects.awaiting_validation()
        .prefetch_related("user")
        .order_by("-key_expires")
    )
    context = {"inactive_contributors": inactive_contributors, "now": timezone.now()}
    return render(request, "scipost/registration_requests.html", context)


@require_POST
@permission_required("scipost.can_resend_registration_requests", return_403=True)
def registration_requests_reset(request, contributor_id):
    """Reset specific activation_key for Contributor and resend activation mail."""
    contributor = get_object_or_404(
        Contributor.objects.awaiting_validation(), id=contributor_id
    )
    contributor.generate_key()
    contributor.save()

    mail_util = DirectMailUtil(
        "contributors/new_activitation_link", contributor=contributor
    )
    mail_util.send_mail()
    messages.success(
        request,
        (
            "New key successfully generated and sent to <i>%s</i>"
            % contributor.user.email
        ),
    )
    return redirect(reverse("scipost:registration_requests"))


class SciPostLoginView(LoginView):
    """
    Login for all types of users.

    Inherits from django.contrib.auth.views:LoginView.

    Overriden fields:

    * template_name
    * authentication_form

    Overriden methods:

    * get initial: allow prefilling with GET data, for 'next'
    * get redirect url
    """

    template_name = "scipost/login.html"
    authentication_form = SciPostAuthenticationForm

    def get_initial(self):
        return self.request.GET

    def get_success_url(self):
        """Add items to session variables."""
        if has_contributor(self.request.user):
            self.request.session["session_acad_field_slug"] = (
                self.request.user.contributor.profile.acad_field.slug
                if self.request.user.contributor.profile.acad_field
                else ""
            )
            if self.request.user.contributor.fellowships.active():
                self.request.session["session_fellowship_id"] = (
                    self.request.user.contributor.fellowships.active().first().id
                )
        return super().get_success_url()

    def get_redirect_url(self):
        """Redirect to the requested url if safe, otherwise to personal page or org dashboard."""
        redirect_to = self.request.POST.get(
            self.redirect_field_name, self.request.GET.get(self.redirect_field_name, "")
        )
        url_is_safe = url_has_allowed_host_and_scheme(
            url=redirect_to,
            allowed_hosts=self.get_success_url_allowed_hosts(),
            require_https=self.request.is_secure(),
        )
        if url_is_safe:
            return redirect_to
        if has_contributor(self.request.user):
            return reverse_lazy("scipost:personal_page")
        elif has_contact(self.request.user):
            return reverse_lazy("organizations:dashboard")
        else:
            return reverse_lazy("scipost:index")


def prompt_to_login(request):
    """Prompt to login before viewing the requested page."""
    return redirect(
        reverse("scipost:login")
        + "?next="
        + urllib.parse.quote(request.get_full_path())
    )


def raw_user_auth_info(request):
    form = UserAuthInfoForm(request.POST or None)

    data = {}
    if form.is_valid():
        data = form.get_data()
    return JsonResponse(data)


class SciPostLogoutView(LogoutView):
    """Logout processing page."""

    next_page = reverse_lazy("scipost:index")

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        """Add message to request after logout."""
        response = super().dispatch(request, *args, **kwargs)
        messages.success(
            request, "<h3>Keep contributing!</h3> You are now logged out of SciPost."
        )
        return response


class SciPostPasswordChangeView(PasswordChangeView):
    """
    Change a user's password (for Contributors and other forms of users).

    Inherits from django.contrib.auth.views:PasswordChangeView.

    Overriden fields:

    * template_name

    Overriden methods:

    * get_success_url
    """

    template_name = "scipost/password_change.html"

    def get_success_url(self):
        """
        Add a message confirming the change, then redirect to personal page.

        For Contributor users, this ends up on the personal page.
        For organization Contacts, this ends up on the organizations dashboard.
        """
        messages.success(
            self.request, "Your SciPost password has been changed successfully."
        )
        return reverse_lazy("scipost:personal_page")


class SciPostPasswordResetView(PasswordResetView):
    """
    Reset a user's password.

    Derived from django.contrib.auth.views:PasswordResetView.

    Overriden fields:

    * template_name
    * email_template_name
    * subject_template_name

    Overriden methods:

    * get_success_url
    """

    template_name = "scipost/password_reset.html"
    email_template_name = "scipost/password_reset_email.html"
    subject_template_name = "scipost/password_reset_subject.txt"

    def get_success_url(self):
        """
        Add a message confirming the request for a new token, then redirect to homepage.
        """
        messages.success(
            self.request,
            (
                "We have just emailed you a password reset token. "
                "Please follow the link in this email to reset your password."
            ),
        )
        return reverse_lazy("scipost:index")


class SciPostPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Confirm reset of password, for all users.

    Derived from django.contrib.auth.views:PasswordResetConfirmView.

    Overriden fields:

    * template_name

    Overriden methods:

    * get_success_url
    """

    template_name = "scipost/password_reset_confirm.html"

    def get_success_url(self):
        """
        Add a message confirming the reset, then redirect to personal page (for
        which login will be required).

        For Contributor users, this ends up on the personal page.
        For organization Contacts, this ends up on the organizations dashboard.
        """
        messages.success(
            self.request,
            (
                "Your SciPost password has been reset successfully. "
                "Please login to see your personal pages."
            ),
        )
        return reverse_lazy("scipost:personal_page")


@login_required
@is_contributor_user()
def _hx_unavailability(request, pk: int = None):
    if pk:  # delete UnavaiabilityPeriod, if asked by associated Contributor
        UnavailabilityPeriod.objects.filter(
            contributor=request.user.contributor,
            pk=pk,
        ).delete()
    form = UnavailabilityPeriodForm(request.POST or None)
    if form.is_valid():
        unav = form.save(commit=False)
        unav.contributor = request.user.contributor
        unav.save()
    context = {"form": form}
    return render(request, "scipost/personal_page/_hx_unavailability.html", context)


@is_contributor_user()
def personal_page(request):
    context = {
        "appellation": str(request.user),
        "needs_validation": False,
    }
    try:
        contributor = request.user.contributor
        context["needs_validation"] = contributor.status != NORMAL_CONTRIBUTOR
    except (Contributor.DoesNotExist, AttributeError):
        if has_contact(request.user):
            return redirect(reverse("organizations:dashboard"))
        contributor = None

    if contributor:
        context["appellation"] = (
            contributor.profile.get_title_display() + " " + contributor.user.last_name
        )
    return render(request, "scipost/personal_page/personal_page.html", context)


@login_required
def personal_page_hx_account(request):
    """Personal Page tab: Account."""
    contributor = request.user.contributor
    context = {
        "contributor": contributor,
    }
    return render(request, "scipost/personal_page/_hx_account.html", context)


@login_required
def personal_page_hx_admin(request):
    """Personal Page tab: Admin Actions."""
    permission = (
        request.user.groups.filter(
            name__in=["SciPost Administrators", "Financial Administrators"]
        ).exists()
        or request.user.is_superuser
    )
    if not permission:
        raise PermissionDenied
    context = {}
    contributor = request.user.contributor
    if contributor.is_scipost_admin:
        # count the number of pending registration requests
        context["nr_reg_to_vet"] = Contributor.objects.awaiting_vetting().count()
        context["nr_reg_awaiting_validation"] = (
            Contributor.objects.awaiting_validation().count()
        )
    return render(request, "scipost/personal_page/_hx_admin.html", context)


@login_required
def personal_page_hx_edadmin(request):
    """
    Personal Page tab: Editorial Actions.
    """
    permission = (
        request.user.groups.filter(
            name__in=[
                "Ambassadors",
                "Advisory Board",
                "Editorial Administrators",
                "Editorial College",
                "Vetting Editors",
                "Junior Ambassadors",
            ]
        ).exists()
        or request.user.is_superuser
    )
    permission = permission or request.user.contributor.is_active_fellow
    if not permission:
        raise PermissionDenied
    context = {}
    contributor = request.user.contributor
    if contributor.is_scipost_admin:
        context["nr_submissions_to_assign"] = Submission.objects.preassignment().count()
        context["nr_recommendations_to_prepare_for_voting"] = (
            EICRecommendation.objects.voting_in_preparation().count()
        )
    if contributor.is_vetting_editor:
        context["nr_commentary_page_requests_to_vet"] = (
            Commentary.objects.awaiting_vetting()
            .exclude(requested_by=contributor)
            .count()
        )
        context["nr_comments_to_vet"] = Comment.objects.awaiting_vetting().count()
        context["nr_thesislink_requests_to_vet"] = (
            ThesisLink.objects.awaiting_vetting().count()
        )
        context["nr_authorship_claims_to_vet"] = (
            AuthorshipClaim.objects.awaiting_vetting().count()
        )
    if contributor.is_active_fellow:
        context["nr_assignments_to_consider"] = (
            contributor.editorial_assignments.invited().count()
        )
        context["active_assignments"] = contributor.editorial_assignments.ongoing()
        context["nr_reports_to_vet"] = (
            Report.objects.awaiting_vetting()
            .filter(submission__editor_in_charge=contributor)
            .count()
        )
    if contributor.is_ed_admin:
        context["nr_reports_without_pdf"] = (
            Report.objects.accepted().filter(pdf_report="").count()
        )
        context["nr_treated_submissions_without_pdf"] = (
            Submission.objects.treated().public().filter(pdf_refereeing_pack="").count()
        )
    return render(request, "scipost/personal_page/_hx_edadmin.html", context)


@login_required
def personal_page_hx_refereeing(request):
    context = {"contributor": request.user.contributor}
    return render(request, "scipost/personal_page/_hx_refereeing.html", context)


@login_required
def personal_page_hx_publications(request):
    """
    Personal Page tab: Publications.
    """
    contributor = request.user.contributor
    context = {
        "contributor": contributor,
        "own_publications": contributor.profile.publications()
        .published()
        .order_by("-publication_date"),
    }
    return render(request, "scipost/personal_page/_hx_publications.html", context)


@login_required
def personal_page_hx_submissions(request):
    """
    Personal Page tab: Submissions.
    """
    contributor = request.user.contributor
    context = {"contributor": contributor}

    context["nr_submission_authorships_to_claim"] = (
        Submission.objects.filter(author_list__contains=request.user.last_name)
        .exclude(authors=contributor)
        .exclude(authors_claims=contributor)
        .exclude(authors_false_claims=contributor)
        .count()
    )
    context["own_submissions"] = contributor.submissions.latest().order_by(
        "-submission_date"
    )
    return render(request, "scipost/personal_page/_hx_submissions.html", context)


@login_required
def personal_page_hx_commentaries(request):
    """
    Personal Page tab: Commentaries.
    """
    contributor = request.user.contributor
    context = {"contributor": contributor}

    context["nr_commentary_authorships_to_claim"] = (
        Commentary.objects.filter(author_list__contains=request.user.last_name)
        .exclude(authors=contributor)
        .exclude(authors_claims=contributor)
        .exclude(authors_false_claims=contributor)
        .count()
    )
    context["own_submissions"] = contributor.commentaries.order_by("-latest_activity")
    return render(request, "scipost/personal_page/_hx_commentaries.html", context)


@login_required
def personal_page_hx_theses(request):
    """
    Personal Page tab: Theses.
    """
    contributor = request.user.contributor
    context = {"contributor": contributor}

    context["nr_thesis_authorships_to_claim"] = (
        ThesisLink.objects.filter(author__contains=request.user.last_name)
        .exclude(author_as_cont=contributor)
        .exclude(author_claims=contributor)
        .exclude(author_false_claims=contributor)
        .count()
    )
    context["own_thesislinks"] = contributor.theses.all()
    return render(request, "scipost/personal_page/_hx_theses.html", context)


@login_required
def personal_page_hx_comments(request):
    """
    Personal Page tab: Comments.
    """
    contributor = request.user.contributor
    context = {
        "contributor": contributor,
        "own_comments": contributor.comments.regular_comments().order_by(
            "-date_submitted"
        ),
    }
    return render(request, "scipost/personal_page/_hx_comments.html", context)


@login_required
def personal_page_hx_author_replies(request):
    """
    Personal Page tab: Author Replies.
    """
    contributor = request.user.contributor
    context = {
        "contributor": contributor,
        "own_authorreplies": contributor.comments.author_replies().order_by(
            "-date_submitted"
        ),
    }
    return render(request, "scipost/personal_page/_hx_author_replies.html", context)


def _update_personal_data_user_only(request):
    user_form = UpdateUserDataForm(request.POST or None, instance=request.user)
    if user_form.is_valid():
        user_form.save()
        messages.success(request, "Your personal data has been updated.")
        return redirect(reverse("scipost:update_personal_data"))
    context = {"user_form": user_form}
    return render(request, "scipost/update_personal_data.html", context)


def _update_personal_data_contact(request):
    contact = Contact.objects.get(user=request.user)
    user_form = UpdateUserDataForm(request.POST or None, instance=request.user)
    contact_form = UpdateContactDataForm(request.POST or None, instance=contact)
    if user_form.is_valid() and contact_form.is_valid():
        user_form.save()
        contact_form.save()
        messages.success(request, "Your personal data has been updated.")
        return redirect(reverse("organizations:dashboard"))

    context = {
        "user_form": user_form,
        "contact_form": contact_form,
    }
    return render(request, "scipost/update_personal_data.html", context)


def _update_personal_data_contributor(request):
    contributor = Contributor.objects.get(user=request.user)
    user_form = UpdateUserDataForm(request.POST or None, instance=request.user)
    cont_form = UpdatePersonalDataForm(request.POST or None, instance=contributor)
    if user_form.is_valid() and cont_form.is_valid():
        user_form.save()
        cont_form.save()
        cont_form.sync_lists()
        if "orcid_id" in cont_form.changed_data:
            cont_form.propagate_orcid()
        messages.success(request, "Your personal data has been updated.")
        return redirect(reverse("scipost:personal_page"))

    context = {
        "user_form": user_form,
        "cont_form": cont_form,
    }
    return render(request, "scipost/update_personal_data.html", context)


@login_required
def update_personal_data(request):
    if has_contributor(request.user):
        return _update_personal_data_contributor(request)
    elif has_contact(request.user):
        return _update_personal_data_contact(request)
    return _update_personal_data_user_only(request)


class TOTPListView(LoginRequiredMixin, ListView):
    """
    List all TOTP devices for logged in User.
    """

    def get_queryset(self):
        return self.request.user.devices.all()


class TOTPDeviceCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """
    Create a new TOTP device.
    """

    form_class = TOTPDeviceForm
    template_name = "scipost/totpdevice_form.html"
    success_url = reverse_lazy("scipost:totp")
    success_message = "Two factor authentication device %(name)s successfully added."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["current_user"] = self.request.user
        return kwargs


class TOTPDeviceDeleteView(LoginRequiredMixin, DeleteView):
    """
    Confirm deletion of a TOTP device.
    """

    pk_url_kwarg = "device_id"
    success_url = reverse_lazy("scipost:totp")

    def get_queryset(self):
        return self.request.user.devices.all()


@login_required
@is_contributor_user()
def claim_authorships(request):
    """
    The system auto-detects potential authorships (of submissions,
    papers subject to commentaries, theses, ...).
    The contributor must confirm/deny authorship from the
    Personal Page.
    """
    contributor = Contributor.objects.get(user=request.user)

    submission_authorships_to_claim = (
        Submission.objects.filter(author_list__contains=contributor.user.last_name)
        .exclude(authors=contributor)
        .exclude(authors_claims=contributor)
        .exclude(authors_false_claims=contributor)
    )
    sub_auth_claim_form = AuthorshipClaimForm()
    commentary_authorships_to_claim = (
        Commentary.objects.filter(author_list__contains=contributor.user.last_name)
        .exclude(authors=contributor)
        .exclude(authors_claims=contributor)
        .exclude(authors_false_claims=contributor)
    )
    com_auth_claim_form = AuthorshipClaimForm()
    thesis_authorships_to_claim = (
        ThesisLink.objects.filter(author__contains=contributor.user.last_name)
        .exclude(author_as_cont=contributor)
        .exclude(author_claims=contributor)
        .exclude(author_false_claims=contributor)
    )
    thesis_auth_claim_form = AuthorshipClaimForm()

    context = {
        "submission_authorships_to_claim": submission_authorships_to_claim,
        "sub_auth_claim_form": sub_auth_claim_form,
        "commentary_authorships_to_claim": commentary_authorships_to_claim,
        "com_auth_claim_form": com_auth_claim_form,
        "thesis_authorships_to_claim": thesis_authorships_to_claim,
        "thesis_auth_claim_form": thesis_auth_claim_form,
    }
    return render(request, "scipost/claim_authorships.html", context)


@login_required
@is_contributor_user()
def claim_sub_authorship(request, submission_id, claim):
    if request.method == "POST":
        contributor = Contributor.objects.get(user=request.user)
        submission = get_object_or_404(Submission, pk=submission_id)
        if claim == 1:
            submission.authors_claims.add(contributor)
            newclaim = AuthorshipClaim(claimant=contributor, submission=submission)
            newclaim.save()
        elif claim == 0:
            submission.authors_false_claims.add(contributor)
        else:
            raise Http404
        submission.save()
    return redirect("scipost:claim_authorships")


@login_required
@is_contributor_user()
def claim_com_authorship(request, commentary_id, claim):
    if request.method == "POST":
        contributor = Contributor.objects.get(user=request.user)
        commentary = get_object_or_404(Commentary, pk=commentary_id)
        if claim == 1:
            commentary.authors_claims.add(contributor)
            newclaim = AuthorshipClaim(claimant=contributor, commentary=commentary)
            newclaim.save()
        elif claim == 0:
            commentary.authors_false_claims.add(contributor)
        else:
            raise Http404
        commentary.save()
    return redirect("scipost:claim_authorships")


@login_required
@is_contributor_user()
def claim_thesis_authorship(request, thesis_id, claim):
    if request.method == "POST":
        contributor = Contributor.objects.get(user=request.user)
        thesislink = get_object_or_404(ThesisLink, pk=thesis_id)
        if claim == 1:
            thesislink.author_claims.add(contributor)
            newclaim = AuthorshipClaim(claimant=contributor, thesislink=thesislink)
            newclaim.save()
        elif claim == 0:
            thesislink.author_false_claims.add(contributor)
        else:
            raise Http404
        thesislink.save()
    return redirect("scipost:claim_authorships")


@permission_required("scipost.can_vet_authorship_claims", return_403=True)
def vet_authorship_claims(request):
    claims_to_vet = AuthorshipClaim.objects.filter(status="0")
    context = {"claims_to_vet": claims_to_vet}
    return render(request, "scipost/vet_authorship_claims.html", context)


@permission_required("scipost.can_vet_authorship_claims", return_403=True)
def vet_authorship_claim(request, claim_id, claim):
    if request.method == "POST":
        vetting_contributor = Contributor.objects.get(user=request.user)
        claim_to_vet = AuthorshipClaim.objects.get(pk=claim_id)

        if claim_to_vet.submission:
            claim_to_vet.submission.authors_claims.remove(claim_to_vet.claimant)
            if claim == 1:
                claim_to_vet.submission.authors.add(claim_to_vet.claimant)
                claim_to_vet.status = "1"
            elif claim == 0:
                claim_to_vet.submission.authors_false_claims.add(claim_to_vet.claimant)
                claim_to_vet.status = "-1"
            claim_to_vet.submission.save()
        if claim_to_vet.commentary:
            claim_to_vet.commentary.authors_claims.remove(claim_to_vet.claimant)
            if claim == 1:
                claim_to_vet.commentary.authors.add(claim_to_vet.claimant)
                claim_to_vet.status = "1"
            elif claim == 0:
                claim_to_vet.commentary.authors_false_claims.add(claim_to_vet.claimant)
                claim_to_vet.status = "-1"
            claim_to_vet.commentary.save()
        if claim_to_vet.thesislink:
            claim_to_vet.thesislink.author_claims.remove(claim_to_vet.claimant)
            if claim == 1:
                claim_to_vet.thesislink.author_as_cont.add(claim_to_vet.claimant)
                claim_to_vet.status = "1"
            elif claim == 0:
                claim_to_vet.thesislink.author_false_claims.add(claim_to_vet.claimant)
                claim_to_vet.status = "-1"
            claim_to_vet.thesislink.save()

        claim_to_vet.vetted_by = vetting_contributor
        claim_to_vet.save()
    return redirect("scipost:vet_authorship_claims")


def contributor_info(request, contributor_id):
    """
    All visitors can see a digest of a
    Contributor's activities/contributions by clicking
    on the relevant name (in listing headers of Submissions, ...).
    """
    contributor = get_object_or_404(Contributor, pk=contributor_id)
    if contributor.duplicate_of:
        messages.warning(
            request,
            (
                "The Contributor you requested is a duplicate; "
                "we redirected you to the original one."
            ),
        )
        return redirect(
            reverse(
                "scipost:contributor_info",
                kwargs={"contributor_id": contributor.duplicate_of.id},
            )
        )

    contributor_publications = []
    if profile := contributor.profile:
        contributor_publications = profile.publications().published()
    contributor_submissions = Submission.objects.public_listed().filter(
        authors=contributor
    )
    contributor_commentaries = Commentary.objects.filter(authors=contributor)
    contributor_theses = ThesisLink.objects.vetted().filter(author_as_cont=contributor)
    contributor_comments = (
        Comment.objects.vetted()
        .publicly_visible()
        .filter(author=contributor, is_author_reply=False)
        .order_by("-date_submitted")
    )
    contributor_authorreplies = (
        Comment.objects.vetted()
        .publicly_visible()
        .filter(author=contributor, is_author_reply=True)
        .order_by("-date_submitted")
    )
    context = {
        "contributor": contributor,
        "contributor_publications": contributor_publications,
        "contributor_submissions": contributor_submissions,
        "contributor_commentaries": contributor_commentaries,
        "contributor_theses": contributor_theses,
        "contributor_comments": contributor_comments,
        "contributor_authorreplies": contributor_authorreplies,
    }
    return render(request, "scipost/contributor_info.html", context)


@permission_required("scipost.can_vet_registration_requests")
def contributor_duplicates(request, group_by: str):
    return render(
        request, "scipost/contributor_duplicates.html", {"group_by": group_by}
    )


class ContributorDuplicateListView(PermissionsMixin, ListView):
    """
    List Contributors with potential (not yet handled) duplicates.
    Two sources of duplicates are separately considered:

    * duplicate full names (last name + first name)
    * duplicate email addresses.

    """

    permission_required = "scipost.can_vet_registration_requests"
    model = Contributor
    template_name = "scipost/_hx_contributor_duplicate_merger.html"

    def get_queryset(self):
        queryset = Contributor.objects.all()
        if self.request.GET.get("kind") == "names":
            queryset = queryset.with_duplicate_names()
        elif self.request.GET.get("kind") == "emails":
            queryset = queryset.with_duplicate_email()
        else:
            queryset = queryset.with_duplicate_names()
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["duplicate_contributors"] = context.pop("object_list")

        if len(context["duplicate_contributors"]) > 1:
            initial = {
                "to_merge": context["duplicate_contributors"][0].id,
                "to_merge_into": context["duplicate_contributors"][1].id,
            }
            context["form"] = ContributorMergeForm(
                initial=initial, queryset=self.get_queryset()
            )
        return context


@transaction.atomic
@permission_required_htmx(
    "scipost.can_merge_contributors",
    "You are not allowed to merge Contributors.",
)
def _hx_contributor_comparison(request):
    """
    Handles the merging of data from one Contributor instance to another,
    to solve one person - multiple registrations issues.

    Both instances are preserved, but the merge_from instance's
    status is set to DOUBLE_ACCOUNT and its User is set to inactive.

    If both Contributor instances were active, then the account owner
    is emailed with information about the merge.
    """

    if request.method == "GET":
        try:
            context = {
                "contributor_to_merge": get_object_or_404(
                    Contributor, pk=int(request.GET["to_merge"])
                ),
                "contributor_to_merge_into": get_object_or_404(
                    Contributor, pk=int(request.GET["to_merge_into"])
                ),
            }
        except ValueError:
            raise Http404

    return render(request, "scipost/_hx_contributor_comparison.html", context)


@transaction.atomic
@permission_required_htmx(
    "scipost.can_merge_contributors",
    "You are not allowed to merge Contributors.",
)
def _hx_contributor_merge(request, to_merge: int, to_merge_into: int):
    """
    Confirms the merging of data from one Contributor instance to another,
    to solve one person - multiple registrations issues.
    """

    post_data = {
        **(request.POST or {}),
        "to_merge": to_merge,
        "to_merge_into": to_merge_into,
    }

    merge_form = ContributorMergeForm(
        post_data,
        queryset=Contributor.objects.filter(id__in=[to_merge, to_merge_into]),
    )

    if request.method == "POST":
        if merge_form.is_valid():
            contributor = merge_form.save()
            messages.success(request, "Contributors merged successfully.")
            return HTMXResponse(
                f"Contributors {to_merge} and {to_merge_into} merged into {contributor.id}.",
            )
        elif to_merge == to_merge_into:
            return HTMXResponse(
                "Cannot merge a Contributor into itself.",
                tag="danger",
            )

    return HTMXResponse(
        "Failed to merge contributors.",
        tag="danger",
    )


####################
# Email facilities #
####################


@permission_required("scipost.can_email_group_members", return_403=True)
def email_group_members(request):
    """
    Method to send bulk emails to (members of) selected groups
    """
    form = EmailGroupMembersForm(request.POST or None)
    if form.is_valid():
        domain = get_current_domain()
        group_members = (
            form.cleaned_data["group"]
            .user_set.filter(contributor__isnull=False)
            .order_by("last_name")
        )  # to make pagination consistent
        p = Paginator(group_members, 32)
        for pagenr in p.page_range:
            page = p.page(pagenr)
            with mail.get_connection() as connection:
                for member in page.object_list:
                    if (
                        member.contributor.profile.accepts_SciPost_emails
                        or member.groups.filter(name="Editorial College").exists()
                    ):  # bypass for Fellows
                        email_text = ""
                        email_text_html = "{% load automarkup %}\n"
                        if form.cleaned_data["personalize"]:
                            email_text = (
                                "Dear "
                                + member.contributor.profile.get_title_display()
                                + " "
                                + member.last_name
                                + ", \n\n"
                            )
                            email_text_html += "Dear {{ title }} {{ last_name }},<br/>"
                        email_text += form.cleaned_data["email_text"]
                        email_text_html += "{% automarkup email_text %}"
                        if form.cleaned_data["include_scipost_summary"]:
                            email_text += SCIPOST_SUMMARY_FOOTER
                            email_text_html += SCIPOST_SUMMARY_FOOTER_HTML
                        email_text_html += EMAIL_FOOTER
                        url_unsubscribe = reverse(
                            "scipost:unsubscribe",
                            args=[
                                member.contributor.id,
                                member.contributor.activation_key,
                            ],
                        )
                        # email_text += ('\n\nDon\'t want to receive such emails? '
                        #                'Unsubscribe by visiting %s.' % url_unsubscribe)
                        # email_text_html += (
                        #     '<br/>\n<p style="font-size: 10px;">Don\'t want to receive such '
                        #     'emails? <a href="%s">Unsubscribe</a>.</p>' % url_unsubscribe)
                        email_context = {
                            "title": member.contributor.profile.get_title_display(),
                            "last_name": member.last_name,
                            "email_text": form.cleaned_data["email_text"],
                            "key": member.contributor.activation_key,
                        }
                        html_template = Template(email_text_html)
                        html_version = html_template.render(Context(email_context))
                        message = EmailMultiAlternatives(
                            form.cleaned_data["email_subject"],
                            email_text,
                            "SciPost Admin <admin@%s>" % domain,
                            [member.email],
                            connection=connection,
                        )
                        message.attach_alternative(html_version, "text/html")
                        message.send()
        context = {
            "ack_header": "The email has been sent.",
            "followup_message": "Return to your ",
            "followup_link": reverse("scipost:personal_page"),
            "followup_link_label": "personal page",
        }
        return render(request, "scipost/acknowledgement.html", context)

    context = {"form": form}
    return render(request, "scipost/email_group_members.html", context)


@permission_required("scipost.can_email_particulars", return_403=True)
def email_particular(request):
    """
    Method to send emails to individuals (registered or not)
    """
    if request.method == "POST":
        form = EmailParticularForm(request.POST)
        if form.is_valid():
            domain = get_current_domain()
            email_text = form.cleaned_data["email_text"]
            email_text_html = "{{ email_text|linebreaks }}"
            email_context = {"email_text": form.cleaned_data["email_text"]}
            if form.cleaned_data["include_scipost_summary"]:
                email_text += SCIPOST_SUMMARY_FOOTER
                email_text_html += SCIPOST_SUMMARY_FOOTER_HTML

            email_text_html += "<br/>" + EMAIL_FOOTER
            html_template = Template(email_text_html)
            html_version = html_template.render(Context(email_context))
            message = EmailMultiAlternatives(
                form.cleaned_data["email_subject"],
                email_text,
                "SciPost Admin <admin@%s>" % domain,
                [form.cleaned_data["email_address"]],
                bcc=["admin@%s" % domain],
            )
            message.attach_alternative(html_version, "text/html")
            message.send()
            context = {
                "ack_header": "The email has been sent.",
                "followup_message": "Return to your ",
                "followup_link": reverse("scipost:personal_page"),
                "followup_link_label": "personal page",
            }
            return render(request, "scipost/acknowledgement.html", context)
    form = EmailParticularForm()
    context = {"form": form}
    return render(request, "scipost/email_particular.html", context)


@permission_required("scipost.can_email_particulars", return_403=True)
def send_precooked_email(request):
    """
    Method to send precooked emails to individuals (registered or not)
    """
    form = SendPrecookedEmailForm(request.POST or None)
    if form.is_valid():
        domain = get_current_domain()
        precookedEmail = form.cleaned_data["email_option"]
        if form.cleaned_data["email_address"] in precookedEmail.emailed_to:
            errormessage = "This message has already been sent to this address"
            return render(
                request, "scipost/error.html", context={"errormessage": errormessage}
            )
        precookedEmail.emailed_to.append(form.cleaned_data["email_address"])
        precookedEmail.date_last_used = timezone.now().date()
        precookedEmail.save()
        email_text = precookedEmail.email_text
        email_text_html = "{{ email_text|linebreaks }}"
        email_context = {"email_text": precookedEmail.email_text_html}
        if form.cleaned_data["include_scipost_summary"]:
            email_text += SCIPOST_SUMMARY_FOOTER
            email_text_html += SCIPOST_SUMMARY_FOOTER_HTML

        email_text_html += "<br/>" + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(Context(email_context))
        message = EmailMultiAlternatives(
            precookedEmail.email_subject,
            email_text,
            SciPost_from_addresses_dict[form.cleaned_data["from_address"]],
            [form.cleaned_data["email_address"]],
            bcc=["admin@%s" % domain],
        )
        message.attach_alternative(html_version, "text/html")
        message.send()
        context = {
            "ack_header": "The email has been sent.",
            "followup_message": "Return to your ",
            "followup_link": reverse("scipost:personal_page"),
            "followup_link_label": "personal page",
        }
        return render(request, "scipost/acknowledgement.html", context)

    context = {"form": form}
    return render(request, "scipost/send_precooked_email.html", context)


#################
# CSRF handling #
#################


def csrf_failure(request, reason=""):
    """CSRF Failure page."""
    return render(request, "csrf-failure.html")


########################
# Pawning verification #
########################


def have_i_been_pwned(request):
    return HttpResponse(settings.HAVE_I_BEEN_PWNED_TOKEN, content_type="text/plain")
