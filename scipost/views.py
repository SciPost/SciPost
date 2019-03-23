__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import json

from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth.views import password_reset, password_reset_confirm
from django.contrib.auth.views import LoginView, LogoutView
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse, reverse_lazy
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect
from django.template import Context, Template
from django.utils.decorators import method_decorator
from django.utils.http import is_safe_url
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.views.generic.list import ListView
from django.views.debug import cleanse_setting
from django.views.static import serve

from guardian.decorators import permission_required
from haystack.generic_views import SearchView

from .constants import (
    SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS, subject_areas_raw_dict,
    SciPost_from_addresses_dict, NORMAL_CONTRIBUTOR)
from .decorators import has_contributor, is_contributor_user
from .models import Contributor, UnavailabilityPeriod, AuthorshipClaim, EditorialCollege
from .forms import (
    SciPostAuthenticationForm, # DEPRECauth AuthenticationForm,
    UnavailabilityPeriodForm, RegistrationForm, AuthorshipClaimForm,
    SearchForm, VetRegistrationForm, reg_ref_dict, UpdatePersonalDataForm, UpdateUserDataForm,
    PasswordChangeForm, ContributorMergeForm,
    EmailGroupMembersForm, EmailParticularForm, SendPrecookedEmailForm)
from .mixins import PermissionsMixin, PaginationMixin
from .utils import Utils, EMAIL_FOOTER, SCIPOST_SUMMARY_FOOTER, SCIPOST_SUMMARY_FOOTER_HTML

from affiliations.forms import AffiliationsFormset
from colleges.permissions import fellowship_or_admin_required
from colleges.models import Fellowship
from commentaries.models import Commentary
from comments.models import Comment
from invitations.constants import STATUS_REGISTERED
from invitations.models import RegistrationInvitation
from journals.models import Journal, Publication, PublicationAuthorsTable
from mails.utils import DirectMailUtil
from news.models import NewsItem
from organizations.decorators import has_contact
from organizations.models import Organization, Contact
from organizations.forms import UpdateContactDataForm
from submissions.models import Submission, RefereeInvitation, Report, EICRecommendation
from theses.models import ThesisLink


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
    publications = Publication.objects.published().order_by('-publication_date')
    commentaries = Commentary.objects.vetted()
    theses = ThesisLink.objects.vetted()
    organizations = Organization.objects.all()
    context = {
        'newsitems': newsitems,
        'journals': journals,
        'contributors': contributors,
        'submissions': submissions,
        'publications': publications,
        'commentaries': commentaries,
        'theses': theses,
        'organizations': organizations,
    }
    return render(request, 'scipost/sitemap.xml', context)


##############
# Utilitites #
##############

# DEPRECauth
# def is_registered(user):
#     """Check if user is a validated user; has at least one permission group."""
#     return user.groups.exists()


class SearchView(SearchView):
    """Search CBV inherited from Haystack."""

    template_name = 'search/search.html'
    form_class = SearchForm

    def get_context_data(self, *args, **kwargs):
        """Update context with some additional information."""
        ctx = super().get_context_data(*args, **kwargs)
        ctx['search_query'] = self.request.GET.get('q')
        ctx['results_count'] = kwargs['object_list'].count()
        return ctx


#############
# Main view
#############

def index(request):
    """Homepage view of SciPost."""
    context = {
        'news_items': NewsItem.objects.homepage().order_by('-date')[:4],
        'latest_newsitem': NewsItem.objects.homepage().order_by('-date').first(),
        'submissions': Submission.objects.public().order_by('-submission_date')[:3],
        # 'journals': Journal.objects.order_by('name'),
        'publications': Publication.objects.published().order_by('-publication_date',
                                                                 '-paper_nr')[:3],
        'current_sponsors': (Organization.objects.with_subsidy_above_and_up_to(5000, 1000000000)
                             | Organization.objects.current_sponsors()),
    }
    return render(request, 'scipost/index.html', context)


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
    context = {'subject_areas_physics': SCIPOST_SUBJECT_AREAS[0][1]}
    return render(request, 'scipost/feeds.html', context)


################
# Contributors:
################

@transaction.atomic
def register(request):
    """
    Contributor registration form page.

    This public registration view shows and processes the form
    that will create new user account requests. After registration
    the Contributor will need to activate its account via the mail
    sent. After activation the user needs to be vetted by the SciPost
    admin.
    """
    if request.user.is_authenticated():
        return redirect(reverse('scipost:personal_page'))

    form = RegistrationForm(request.POST or None)
    if form.is_valid():
        contributor = form.create_and_save_contributor()
        mail_util = DirectMailUtil('contributors/registration_received', contributor=contributor)
        mail_util.send_mail()

        # Disable invitations related to the new Contributor
        RegistrationInvitation.objects.declined_or_without_response().filter(
            email=form.cleaned_data['email']).update(status=STATUS_REGISTERED)

        context = {
            'ack_header': 'Thanks for registering to SciPost.',
            'ack_message': ('You will receive an email with a link to verify '
                            'your email address. '
                            'Please visit this link within 48 hours. '
                            'Your credentials will thereafter be verified. '
                            'If your registration is vetted through by the '
                            'administrators, you will be enabled to contribute.'),
        }
        return render(request, 'scipost/acknowledgement.html', context)
    return render(request, 'scipost/register.html', {'form': form, 'invited': False})


def invitation(request, key):
    """Registration Invitation reception page.

    If a scientist has recieved an invitation (RegistrationInvitation)
    he/she will finish it's invitation via still view which will prefill
    the default registration form.
    """
    invitation = get_object_or_404(RegistrationInvitation, invitation_key=key)
    if invitation.has_responded:
        errormessage = ('This invitation token has already been used, '
                        'or this email address is already associated to a registration.')
    elif timezone.now() > invitation.key_expires:
        errormessage = 'The invitation key has expired.'
    else:
        context = {
            'invitation': invitation,
            'form': RegistrationForm(initial=invitation.__dict__)
        }
        return render(request, 'scipost/register.html', context)
    return render(request, 'scipost/accept_invitation_error.html', {'errormessage': errormessage})


def activation(request, contributor_id, key):
    """
    After registration, an email verification link is sent.
    Once clicked, the account is activated.
    """
    contributor = get_object_or_404(Contributor, id=contributor_id, activation_key=key)
    if not contributor.user.is_active:
        if timezone.now() > contributor.key_expires:
            return redirect(reverse('scipost:request_new_activation_link', kwargs={
                'contributor_id': contributor_id,
                'key': key
            }))
        contributor.user.is_active = True
        contributor.user.save()
        context = {'ack_header': 'Many thanks for confirming your email address.',
                   'ack_message': ('Your SciPost account will soon be vetted by '
                                   'an administrator, after which you will be able to log in. '
                                   'You will soon receive an email confirmation from us!'),
                   }
        return render(request, 'scipost/acknowledgement.html', context)
    messages.success(request, ('<h3>Your email has already been confirmed.</h3>'
                               'Please wait for vetting of your registration.'
                               ' We shall strive to send you an update by email within 24 hours.'))
    return redirect(reverse('scipost:index'))


def request_new_activation_link(request, contributor_id, key):
    """
    Once a user tries to activate its account using the email verification link sent
    and the key has expired, the user redirected to possibly request a new token.
    """
    contributor = get_object_or_404(Contributor, id=contributor_id, activation_key=key)
    if request.GET.get('confirm', False):
        # Generate a new email activation key and link
        contributor.generate_key()
        contributor.save()

        mail_util = DirectMailUtil('contributors/new_activitation_link', contributor=contributor)
        mail_util.send_mail()

        context = {
            'ack_header': 'We have emailed you a new activation link.',
            'ack_message': ('Please acknowledge it within its 48 hours validity '
                            'window if you want us to proceed with vetting your registration.'),
        }
        return render(request, 'scipost/acknowledgement.html', context)
    context = {'contributor': contributor}
    return render(request, 'scipost/request_new_activation_link.html', context)


def unsubscribe(request, contributor_id, key):
    """
    The link to this method is included in all email communications
    with a Contributor. The key used is the original activation key.
    At this link, the Contributor can confirm that he/she does not
    want to receive any non-essential email notifications from SciPost.
    """
    contributor = get_object_or_404(Contributor, id=contributor_id, activation_key=key)
    if request.GET.get('confirm', False):
        contributor.accepts_SciPost_emails = False
        contributor.save()
        text = ('<h3>We have recorded your preference</h3>'
                'You will no longer receive non-essential email from SciPost.')
        messages.success(request, text)
        return redirect(reverse('scipost:index'))
    return render(request, 'scipost/unsubscribe.html', {'contributor': contributor})


@permission_required('scipost.can_vet_registration_requests', return_403=True)
def vet_registration_requests(request):
    """List of new Registration requests to vet."""
    contributors_to_vet = Contributor.objects.awaiting_vetting().order_by('key_expires')
    form = VetRegistrationForm()
    context = {'contributors_to_vet': contributors_to_vet, 'form': form}
    return render(request, 'scipost/vet_registration_requests.html', context)


@permission_required('scipost.can_vet_registration_requests', return_403=True)
def vet_registration_request_ack(request, contributor_id):
    """Form view to vet new Registration requests."""
    form = VetRegistrationForm(request.POST or None)
    contributor = Contributor.objects.get(pk=contributor_id)
    if form.is_valid():
        if form.promote_to_registered_contributor():
            contributor.status = NORMAL_CONTRIBUTOR
            contributor.vetted_by = request.user.contributor
            contributor.save()
            group = Group.objects.get(name='Registered Contributors')
            contributor.user.groups.add(group)

            # Verify if there is a pending refereeing invitation using email and invitation key.
            updated_rows = RefereeInvitation.objects.open().filter(
                referee__isnull=True,
                email_address=contributor.user.email).update(referee=contributor)
            if contributor.invitation_key:
                updated_rows += RefereeInvitation.objects.open().filter(
                    referee__isnull=True,
                    invitation_key=contributor.invitation_key).update(referee=contributor)
            pending_ref_inv_exists = updated_rows > 0

            email_text = (
                'Dear ' + contributor.get_title_display() + ' ' + contributor.user.last_name +
                ', \n\nYour registration to the SciPost publication portal has been accepted. '
                'You can now login at https://scipost.org and contribute. \n\n')
            if pending_ref_inv_exists:
                email_text += (
                    'Note that you have pending refereeing invitations; please navigate to '
                    'https://scipost.org/submissions/accept_or_decline_ref_invitations '
                    '(login required) to accept or decline them.\n\n')
            email_text += 'Thank you very much in advance, \nThe SciPost Team.'
            emailmessage = EmailMessage('SciPost registration accepted', email_text,
                                        'SciPost registration <registration@scipost.org>',
                                        [contributor.user.email],
                                        bcc=['registration@scipost.org'],
                                        reply_to=['registration@scipost.org'])
            emailmessage.send(fail_silently=False)
        else:
            ref_reason = form.cleaned_data['refusal_reason']
            email_text = (
                'Dear ' + contributor.get_title_display() + ' ' + contributor.user.last_name +
                ', \n\nYour registration to the SciPost publication portal has been turned down,'
                ' the reason being: ' + reg_ref_dict[ref_reason] + '. You can however still view '
                'all SciPost contents, just not submit papers, comments or votes. We nonetheless '
                'thank you for your interest.\n\nThe SciPost Team.')
            if form.cleaned_data['email_response_field']:
                email_text += (
                    '\n\nFurther explanations: ' + form.cleaned_data['email_response_field'])
            emailmessage = EmailMessage('SciPost registration: unsuccessful',
                                        email_text,
                                        'SciPost registration <registration@scipost.org>',
                                        [contributor.user.email],
                                        bcc=['registration@scipost.org'],
                                        reply_to=['registration@scipost.org'])
            emailmessage.send(fail_silently=False)
            contributor.status = form.cleaned_data['refusal_reason']
            contributor.save()

    messages.success(request, 'SciPost Registration request vetted.')
    return redirect(reverse('scipost:vet_registration_requests'))


@permission_required('scipost.can_resend_registration_requests', return_403=True)
def registration_requests(request):
    '''
    List all inactive users. These are users that have filled the registration form,
    but did not yet activate their account using the validation email.
    '''
    inactive_contributors = (Contributor.objects.awaiting_validation()
                             .prefetch_related('user')
                             .order_by('-key_expires'))
    context = {
        'inactive_contributors': inactive_contributors,
        'now': timezone.now()
    }
    return render(request, 'scipost/registration_requests.html', context)


@require_POST
@permission_required('scipost.can_resend_registration_requests', return_403=True)
def registration_requests_reset(request, contributor_id):
    """Reset specific activation_key for Contributor and resend activation mail."""
    contributor = get_object_or_404(Contributor.objects.awaiting_validation(), id=contributor_id)
    contributor.generate_key()
    contributor.save()

    mail_util = DirectMailUtil('contributors/new_activitation_link', contributor=contributor)
    mail_util.send_mail()
    messages.success(request, ('New key successfully generated and sent to <i>%s</i>'
                               % contributor.user.email))
    return redirect(reverse('scipost:registration_requests'))


# DEPRECauth
# def login_view(request):
#     """Login form page."""
#     form = AuthenticationForm(request.POST or None, initial=request.GET)
#     if form.is_valid():
#         user = form.authenticate()
#         if user is not None:
#             if is_registered(user):
#                 login(request, user)
#                 redirect_to = form.get_redirect_url(request)
#                 return redirect(redirect_to)
#             else:
#                 form.add_error(None, ('Your account has not yet been vetted. '
#                                       '(our admins will verify your credentials very soon)'))
#         elif form.user_is_inactive():
#             form.add_error(None, ('Your account is not yet activated. '
#                                   'Please first activate your account by clicking on the '
#                                   'activation link we emailed you.'))
#         else:
#             form.add_error(None, 'Invalid username/password.')
#     context = {'form': form}
#     return render(request, 'scipost/login.html', context)


class SciPostLoginView(LoginView):
    """
    Login for all types of users.

    Inherits from django.contrib.auth.views:LoginView.

    Overriden methods:
    - get initial: allow prefilling with GET data, for 'next'
    - get redirect url
    """

    template_name = 'scipost/login.html'
    authentication_form = SciPostAuthenticationForm

    def get_initial(self):
        return self.request.GET

    def get_redirect_url(self):
        """Redirect to the requested url if safe, otherwise to personal page or org dashboard."""
        redirect_to = self.request.POST.get(
            self.redirect_field_name,
            self.request.GET.get(self.redirect_field_name, '')
        )
        url_is_safe = is_safe_url(
            url=redirect_to,
            allowed_hosts=self.get_success_url_allowed_hosts(),
            require_https=self.request.is_secure(),
        )
        if url_is_safe:
            return redirect_to
        if has_contributor(self.request.user):
            return reverse_lazy('scipost:personal_page')
        elif has_contact(self.request.user):
            return reverse_lazy('organizations:dashboard')
        else:
            return reverse_lazy('scipost:index')


class SciPostLogoutView(LogoutView):
    """Logout processing page."""

    next_page = reverse_lazy('scipost:index')
    redirect_field_name = 'next'

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        """Add message to request after logout."""
        response = super().dispatch(request, *args, **kwargs)
        messages.success(request, '<h3>Keep contributing!</h3> You are now logged out of SciPost.')
        return response


@login_required
@is_contributor_user()
def mark_unavailable_period(request):
    """Form view to mark period unavailable for Contributor."""
    unav_form = UnavailabilityPeriodForm(request.POST or None)
    if unav_form.is_valid():
        unav = unav_form.save(commit=False)
        unav.contributor = request.user.contributor
        unav.save()
        messages.success(request, 'Unavailability period registered')
        return redirect('scipost:personal_page')

    # Template acts as a backup in case the form is invalid.
    context = {'form': unav_form}
    return render(request, 'scipost/unavailability_period_form.html', context)


@require_POST
@login_required
@is_contributor_user()
def delete_unavailable_period(request, period_id):
    """Delete period unavailable registered."""
    unav = get_object_or_404(UnavailabilityPeriod,
                             contributor=request.user.contributor, id=int(period_id))
    unav.delete()
    messages.success(request, 'Unavailability period deleted')
    return redirect('scipost:personal_page')


@login_required
@is_contributor_user()
def _personal_page_account(request):
    """ Personal Page tab: Account. """
    contributor = request.user.contributor
    context = {
        'contributor': contributor,
        'unavailability_form': UnavailabilityPeriodForm(),
        'unavailabilities': contributor.unavailability_periods.future().order_by('start')
    }
    return render(request, 'partials/scipost/personal_page/account.html', context)


@login_required
@is_contributor_user()
def _personal_page_admin_actions(request):
    """ Personal Page tab: Admin Actions. """
    permission = request.user.groups.filter(name__in=[
        'SciPost Administrators',
        'Financial Administrators']).exists() or request.user.is_superuser

    if not permission:
        raise PermissionDenied

    context = {}
    contributor = request.user.contributor

    if contributor.is_SP_Admin():
        # count the number of pending registration requests
        context['nr_reg_to_vet'] = Contributor.objects.awaiting_vetting().count()
        context['nr_reg_awaiting_validation'] = Contributor.objects.awaiting_validation().count()

    return render(request, 'partials/scipost/personal_page/admin_actions.html', context)


@is_contributor_user()
def _personal_page_editorial_actions(request):
    """
    Personal Page tab: Editorial Actions.
    """
    permission = request.user.groups.filter(name__in=[
        'Ambassadors',
        'Advisory Board',
        'Editorial Administrators',
        'Editorial College',
        'Vetting Editors',
        'Junior Ambassadors']).exists() or request.user.is_superuser
    permission = permission or request.user.contributor.is_MEC()

    if not permission:
        raise PermissionDenied

    context = {}
    contributor = request.user.contributor

    if contributor.is_SP_Admin():
        context['nr_submissions_to_assign'] = Submission.objects.prescreening().count()
        context['nr_recommendations_to_prepare_for_voting'] = \
            EICRecommendation.objects.voting_in_preparation().count()

    if contributor.is_VE():
        context['nr_commentary_page_requests_to_vet'] = (Commentary.objects.awaiting_vetting()
                                                         .exclude(requested_by=contributor).count())
        context['nr_comments_to_vet'] = Comment.objects.awaiting_vetting().count()
        context['nr_thesislink_requests_to_vet'] = ThesisLink.objects.awaiting_vetting().count()
        context['nr_authorship_claims_to_vet'] = AuthorshipClaim.objects.awaiting_vetting().count()

    if contributor.is_MEC():
        context['nr_assignments_to_consider'] = contributor.editorial_assignments.invited().count()
        context['active_assignments'] = contributor.editorial_assignments.ongoing()
        context['nr_reports_to_vet'] = Report.objects.awaiting_vetting().filter(
            submission__editor_in_charge=contributor).count()

    if contributor.is_EdCol_Admin():
        context['nr_reports_without_pdf'] = Report.objects.accepted().filter(pdf_report='').count()
        context['nr_treated_submissions_without_pdf'] = Submission.objects.treated().public().filter(
            pdf_refereeing_pack='').count()

    return render(request, 'partials/scipost/personal_page/editorial_actions.html', context)


@permission_required('scipost.can_referee', return_403=True)
@is_contributor_user()
def _personal_page_refereeing(request):
    """
    Personal Page tab: Refereeing.
    """
    context = {
        'contributor': request.user.contributor
    }
    return render(request, 'partials/scipost/personal_page/refereeing.html', context)


@login_required
@is_contributor_user()
def _personal_page_publications(request):
    """
    Personal Page tab: Publications.
    """
    contributor = request.user.contributor
    context = {
        'contributor': contributor,
        'own_publications': contributor.publications.published().order_by('-publication_date')
    }
    context['nr_publication_authorships_to_claim'] = Publication.objects.filter(
        author_list__contains=request.user.last_name).exclude(
        authors_registered=contributor).exclude(
        authors_claims=contributor).exclude(
        authors_false_claims=contributor).count()
    return render(request, 'partials/scipost/personal_page/publications.html', context)


@login_required
@is_contributor_user()
def _personal_page_submissions(request):
    """
    Personal Page tab: Submissions.
    """
    contributor = request.user.contributor
    context = {'contributor': contributor}

    context['nr_submission_authorships_to_claim'] = Submission.objects.filter(
        author_list__contains=request.user.last_name).exclude(
        authors=contributor).exclude(
        authors_claims=contributor).exclude(
        authors_false_claims=contributor).count()
    context['own_submissions'] = contributor.submissions.filter(
        is_current=True).order_by('-submission_date')
    return render(request, 'partials/scipost/personal_page/submissions.html', context)


@login_required
@is_contributor_user()
def _personal_page_commentaries(request):
    """
    Personal Page tab: Commentaries.
    """
    contributor = request.user.contributor
    context = {'contributor': contributor}

    context['nr_commentary_authorships_to_claim'] = Commentary.objects.filter(
        author_list__contains=request.user.last_name).exclude(
        authors=contributor).exclude(
        authors_claims=contributor).exclude(
        authors_false_claims=contributor).count()
    context['own_submissions'] = contributor.commentaries.order_by('-latest_activity')
    return render(request, 'partials/scipost/personal_page/commentaries.html', context)


@login_required
@is_contributor_user()
def _personal_page_theses(request):
    """
    Personal Page tab: Theses.
    """
    contributor = request.user.contributor
    context = {'contributor': contributor}

    context['nr_thesis_authorships_to_claim'] = ThesisLink.objects.filter(
        author__contains=request.user.last_name).exclude(
        author_as_cont=contributor).exclude(
        author_claims=contributor).exclude(
        author_false_claims=contributor).count()
    context['own_thesislinks'] = contributor.theses.all()
    return render(request, 'partials/scipost/personal_page/theses.html', context)


@login_required
@is_contributor_user()
def _personal_page_comments(request):
    """
    Personal Page tab: Comments.
    """
    contributor = request.user.contributor
    context = {
        'contributor': contributor,
        'own_comments': contributor.comments.regular_comments().order_by('-date_submitted')
    }

    return render(request, 'partials/scipost/personal_page/comments.html', context)


@login_required
@is_contributor_user()
def _personal_page_author_replies(request):
    """
    Personal Page tab: Author Replies.
    """
    contributor = request.user.contributor
    context = {
        'contributor': contributor,
        'own_authorreplies': contributor.comments.author_replies().order_by('-date_submitted'),
    }

    return render(request, 'partials/scipost/personal_page/author_replies.html', context)


@login_required
def personal_page(request, tab='account'):
    """
    Personal Page is the main view for accessing user functions.
    """
    if request.is_ajax():
        if tab == 'account':
            return _personal_page_account(request)
        elif tab == 'admin_actions':
            return _personal_page_admin_actions(request)
        elif tab == 'editorial_actions':
            return _personal_page_editorial_actions(request)
        elif tab == 'refereeing':
            return _personal_page_refereeing(request)
        elif tab == 'publications':
            return _personal_page_publications(request)
        elif tab == 'submissions':
            return _personal_page_submissions(request)
        elif tab == 'commentaries':
            return _personal_page_commentaries(request)
        elif tab == 'theses':
            return _personal_page_theses(request)
        elif tab == 'comments':
            return _personal_page_comments(request)
        elif tab == 'author_replies':
            return _personal_page_author_replies(request)
        raise Http404

    context = {
        'appellation': str(request.user),
        'needs_validation': False,
        'tab': tab,
    }

    try:
        contributor = Contributor.objects.select_related('user').get(user=request.user)
        context['needs_validation'] = contributor.status != NORMAL_CONTRIBUTOR
    except Contributor.DoesNotExist:
        if has_contact(request.user):
            return redirect(reverse('organizations:dashboard'))
        contributor = None

    if contributor:
        # Refereeing
        refereeing_tab_total_count = contributor.referee_invitations.open().count()
        refereeing_tab_total_count += contributor.referee_invitations.in_process().count()
        refereeing_tab_total_count += contributor.reports.in_draft().count()

        context['refereeing_tab_total_count'] = refereeing_tab_total_count
        context['appellation'] = contributor.get_title_display() + ' ' + contributor.user.last_name
        context['contributor'] = contributor

    return render(request, 'scipost/personal_page.html', context)


@login_required
def change_password(request):
    """Change password form view."""
    form = PasswordChangeForm(request.POST or None, current_user=request.user)
    if form.is_valid():
        form.save_new_password()
        # Update user's session hash to stay logged in.
        update_session_auth_hash(request, request.user)
        messages.success(request, 'Your SciPost password has been successfully changed')
        try:
            request.user.contributor
            return redirect(reverse('scipost:personal_page'))
        except Contributor.DoesNotExist:
            return redirect(reverse('scipost:index'))
    return render(request, 'scipost/change_password.html', {'form': form})


def reset_password_confirm(request, uidb64=None, token=None):
    return password_reset_confirm(request, template_name='scipost/reset_password_confirm.html',
                                  uidb64=uidb64, token=token,
                                  post_reset_redirect=reverse('scipost:login'))


def reset_password(request):
    return password_reset(request, template_name='scipost/reset_password.html',
                          email_template_name='scipost/reset_password_email.html',
                          subject_template_name='scipost/reset_password_subject.txt',
                          post_reset_redirect=reverse('scipost:login'))


def _update_personal_data_user_only(request):
    user_form = UpdateUserDataForm(request.POST or None, instance=request.user)
    if user_form.is_valid():
        user_form.save()
        messages.success(request, 'Your personal data has been updated.')
        return redirect(reverse('scipost:update_personal_data'))
    context = {
        'user_form': user_form
    }
    return render(request, 'scipost/update_personal_data.html', context)


def _update_personal_data_contact(request):
    contact = Contact.objects.get(user=request.user)
    user_form = UpdateUserDataForm(request.POST or None, instance=request.user)
    contact_form = UpdateContactDataForm(request.POST or None, instance=contact)
    if user_form.is_valid() and contact_form.is_valid():
        user_form.save()
        contact_form.save()
        messages.success(request, 'Your personal data has been updated.')
        return redirect(reverse('organizations:dashboard'))

    context = {
        'user_form': user_form,
        'contact_form': contact_form,
    }
    return render(request, 'scipost/update_personal_data.html', context)


def _update_personal_data_contributor(request):
    contributor = Contributor.objects.get(user=request.user)
    user_form = UpdateUserDataForm(request.POST or None, instance=request.user)
    cont_form = UpdatePersonalDataForm(request.POST or None, instance=contributor)
    institution_formset = AffiliationsFormset(request.POST or None, contributor=contributor)
    if user_form.is_valid() and cont_form.is_valid() and institution_formset.is_valid():
        user_form.save()
        cont_form.save()
        cont_form.sync_lists()
        institution_formset.save()
        if 'orcid_id' in cont_form.changed_data:
            cont_form.propagate_orcid()
        messages.success(request, 'Your personal data has been updated.')
        return redirect(reverse('scipost:update_personal_data'))

    context = {
        'user_form': user_form,
        'cont_form': cont_form,
        'institution_formset': institution_formset,
    }
    return render(request, 'scipost/update_personal_data.html', context)


@login_required
def update_personal_data(request):
    if has_contributor(request.user):
        return _update_personal_data_contributor(request)
    elif has_contact(request.user):
        return _update_personal_data_contact(request)
    return _update_personal_data_user_only(request)


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

    publication_authorships_to_claim = (Publication.objects
                                        .filter(author_list__contains=contributor.user.last_name)
                                        .exclude(authors_registered=contributor)
                                        .exclude(authors_claims=contributor)
                                        .exclude(authors_false_claims=contributor))
    pub_auth_claim_form = AuthorshipClaimForm()
    submission_authorships_to_claim = (Submission.objects
                                       .filter(author_list__contains=contributor.user.last_name)
                                       .exclude(authors=contributor)
                                       .exclude(authors_claims=contributor)
                                       .exclude(authors_false_claims=contributor))
    sub_auth_claim_form = AuthorshipClaimForm()
    commentary_authorships_to_claim = (Commentary.objects
                                       .filter(author_list__contains=contributor.user.last_name)
                                       .exclude(authors=contributor)
                                       .exclude(authors_claims=contributor)
                                       .exclude(authors_false_claims=contributor))
    com_auth_claim_form = AuthorshipClaimForm()
    thesis_authorships_to_claim = (ThesisLink.objects
                                   .filter(author__contains=contributor.user.last_name)
                                   .exclude(author_as_cont=contributor)
                                   .exclude(author_claims=contributor)
                                   .exclude(author_false_claims=contributor))
    thesis_auth_claim_form = AuthorshipClaimForm()

    context = {
        'publication_authorships_to_claim': publication_authorships_to_claim,
        'pub_auth_claim_form': pub_auth_claim_form,
        'submission_authorships_to_claim': submission_authorships_to_claim,
        'sub_auth_claim_form': sub_auth_claim_form,
        'commentary_authorships_to_claim': commentary_authorships_to_claim,
        'com_auth_claim_form': com_auth_claim_form,
        'thesis_authorships_to_claim': thesis_authorships_to_claim,
        'thesis_auth_claim_form': thesis_auth_claim_form,
    }
    return render(request, 'scipost/claim_authorships.html', context)


@login_required
@is_contributor_user()
def claim_pub_authorship(request, publication_id, claim):
    if request.method == 'POST':
        contributor = Contributor.objects.get(user=request.user)
        publication = get_object_or_404(Publication, pk=publication_id)
        if claim == '1':
            publication.authors_claims.add(contributor)
            newclaim = AuthorshipClaim(claimant=contributor, publication=publication)
            newclaim.save()
        elif claim == '0':
            publication.authors_false_claims.add(contributor)
        publication.save()
    return redirect('scipost:claim_authorships')


@login_required
@is_contributor_user()
def claim_sub_authorship(request, submission_id, claim):
    if request.method == 'POST':
        contributor = Contributor.objects.get(user=request.user)
        submission = get_object_or_404(Submission, pk=submission_id)
        if claim == '1':
            submission.authors_claims.add(contributor)
            newclaim = AuthorshipClaim(claimant=contributor, submission=submission)
            newclaim.save()
        elif claim == '0':
            submission.authors_false_claims.add(contributor)
        submission.save()
    return redirect('scipost:claim_authorships')


@login_required
@is_contributor_user()
def claim_com_authorship(request, commentary_id, claim):
    if request.method == 'POST':
        contributor = Contributor.objects.get(user=request.user)
        commentary = get_object_or_404(Commentary, pk=commentary_id)
        if claim == '1':
            commentary.authors_claims.add(contributor)
            newclaim = AuthorshipClaim(claimant=contributor, commentary=commentary)
            newclaim.save()
        elif claim == '0':
            commentary.authors_false_claims.add(contributor)
        commentary.save()
    return redirect('scipost:claim_authorships')


@login_required
@is_contributor_user()
def claim_thesis_authorship(request, thesis_id, claim):
    if request.method == 'POST':
        contributor = Contributor.objects.get(user=request.user)
        thesislink = get_object_or_404(ThesisLink, pk=thesis_id)
        if claim == '1':
            thesislink.author_claims.add(contributor)
            newclaim = AuthorshipClaim(claimant=contributor, thesislink=thesislink)
            newclaim.save()
        elif claim == '0':
            thesislink.author_false_claims.add(contributor)
        thesislink.save()
    return redirect('scipost:claim_authorships')


@permission_required('scipost.can_vet_authorship_claims', return_403=True)
def vet_authorship_claims(request):
    claims_to_vet = AuthorshipClaim.objects.filter(status='0')
    context = {'claims_to_vet': claims_to_vet}
    return render(request, 'scipost/vet_authorship_claims.html', context)


@permission_required('scipost.can_vet_authorship_claims', return_403=True)
def vet_authorship_claim(request, claim_id, claim):
    if request.method == 'POST':
        vetting_contributor = Contributor.objects.get(user=request.user)
        claim_to_vet = AuthorshipClaim.objects.get(pk=claim_id)

        if claim_to_vet.publication:
            claim_to_vet.publication.authors_claims.remove(claim_to_vet.claimant)
            if claim == '1':
                PublicationAuthorsTable.objects.create(
                    publication=claim_to_vet.publication, contributor=claim_to_vet.claimant)
                claim_to_vet.status = '1'
            elif claim == '0':
                claim_to_vet.publication.authors_false_claims.add(claim_to_vet.claimant)
                claim_to_vet.status = '-1'
            claim_to_vet.publication.save()
        if claim_to_vet.submission:
            claim_to_vet.submission.authors_claims.remove(claim_to_vet.claimant)
            if claim == '1':
                claim_to_vet.submission.authors.add(claim_to_vet.claimant)
                claim_to_vet.status = '1'
            elif claim == '0':
                claim_to_vet.submission.authors_false_claims.add(claim_to_vet.claimant)
                claim_to_vet.status = '-1'
            claim_to_vet.submission.save()
        if claim_to_vet.commentary:
            claim_to_vet.commentary.authors_claims.remove(claim_to_vet.claimant)
            if claim == '1':
                claim_to_vet.commentary.authors.add(claim_to_vet.claimant)
                claim_to_vet.status = '1'
            elif claim == '0':
                claim_to_vet.commentary.authors_false_claims.add(claim_to_vet.claimant)
                claim_to_vet.status = '-1'
            claim_to_vet.commentary.save()
        if claim_to_vet.thesislink:
            claim_to_vet.thesislink.author_claims.remove(claim_to_vet.claimant)
            if claim == '1':
                claim_to_vet.thesislink.author_as_cont.add(claim_to_vet.claimant)
                claim_to_vet.status = '1'
            elif claim == '0':
                claim_to_vet.thesislink.author_false_claims.add(claim_to_vet.claimant)
                claim_to_vet.status = '-1'
            claim_to_vet.thesislink.save()

        claim_to_vet.vetted_by = vetting_contributor
        claim_to_vet.save()
    return redirect('scipost:vet_authorship_claims')


def contributor_info(request, contributor_id):
    """
    All visitors can see a digest of a
    Contributor's activities/contributions by clicking
    on the relevant name (in listing headers of Submissions, ...).
    """
    contributor = get_object_or_404(Contributor, pk=contributor_id)
    contributor_publications = Publication.objects.published().filter(authors_registered=contributor)
    contributor_submissions = Submission.objects.public_listed().filter(authors=contributor)
    contributor_commentaries = Commentary.objects.filter(authors=contributor)
    contributor_theses = ThesisLink.objects.vetted().filter(author_as_cont=contributor)
    contributor_comments = (Comment.objects.vetted().publicly_visible()
                            .filter(author=contributor, is_author_reply=False)
                            .order_by('-date_submitted'))
    contributor_authorreplies = (Comment.objects.vetted().publicly_visible()
                                 .filter(author=contributor, is_author_reply=True)
                                 .order_by('-date_submitted'))
    context = {'contributor': contributor,
               'contributor_publications': contributor_publications,
               'contributor_submissions': contributor_submissions,
               'contributor_commentaries': contributor_commentaries,
               'contributor_theses': contributor_theses,
               'contributor_comments': contributor_comments,
               'contributor_authorreplies': contributor_authorreplies}
    return render(request, 'scipost/contributor_info.html', context)


class ContributorDuplicateListView(PermissionsMixin, PaginationMixin, ListView):
    """
    List Contributors with potential (not yet handled) duplicates.
    Two sources of duplicates are separately considered:
    - duplicate full names (last name + first name)
    - duplicate email addresses.

    """
    permission_required = 'scipost.can_vet_registration_requests'
    model = Contributor
    template_name = 'scipost/contributor_duplicate_list.html'

    def get_queryset(self):
        queryset = Contributor.objects.all()
        if self.request.GET.get('kind') == 'names':
            queryset = queryset.with_duplicate_names()
        elif self.request.GET.get('kind') == 'emails':
            queryset = queryset.with_duplicate_emails()
        else:
            queryset = queryset.with_duplicate_names()
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        if len(context['object_list']) > 1:
            initial = {
                'to_merge': context['object_list'][0].id,
                'to_merge_into': context['object_list'][1].id
                }
            context['merge_form'] = ContributorMergeForm(initial=initial)
        return context


@transaction.atomic
@permission_required('scipost.can_vet_registration_requests')
def contributor_merge(request):
    """
    Handles the merging of data from one Contributor instance to another,
    to solve one person - multiple registrations issues.

    Both instances are preserved, but the merge_from instance's
    status is set to DOUBLE_ACCOUNT and its User is set to inactive.

    If both Contributor instances were active, then the account owner
    is emailed with information about the merge.
    """
    merge_form = ContributorMergeForm(request.POST or None, initial=request.GET)
    context = {'merge_form': merge_form}

    if request.method == 'POST':
        if merge_form.is_valid():
            contributor = merge_form.save()
            messages.success(request, 'Contributors merged')
            return redirect(reverse('scipost:contributor_duplicates'))
        else:
            try:
                context.update({
                    'contributor_to_merge': get_object_or_404(
                        Contributor, pk=merge_form.cleaned_data['to_merge'].id),
                    'contributor_to_merge_into': get_object_or_404(
                        Contributor, pk=merge_form.cleaned_data['to_merge_into'].id)
                })
            except ValueError:
                raise Http404

    elif request.method == 'GET':
        try:
            context.update({
                'contributor_to_merge': get_object_or_404(Contributor,
                                                          pk=int(request.GET['to_merge'])),
                'contributor_to_merge_into': get_object_or_404(Contributor,
                                                               pk=int(request.GET['to_merge_into'])),
                })
        except ValueError:
            raise Http404

    return render(request, 'scipost/contributor_merge.html', context)


####################
# Email facilities #
####################


@permission_required('scipost.can_email_group_members', return_403=True)
def email_group_members(request):
    """
    Method to send bulk emails to (members of) selected groups
    """
    form = EmailGroupMembersForm(request.POST or None)
    if form.is_valid():
        group_members = form.cleaned_data['group'].user_set.filter(contributor__isnull=False)
        p = Paginator(group_members, 32)
        for pagenr in p.page_range:
            page = p.page(pagenr)
            with mail.get_connection() as connection:
                for member in page.object_list:
                    if member.contributor.accepts_SciPost_emails:
                        email_text = ''
                        email_text_html = ''
                        if form.cleaned_data['personalize']:
                            email_text = ('Dear ' + member.contributor.get_title_display()
                                          + ' ' + member.last_name + ', \n\n')
                            email_text_html = 'Dear {{ title }} {{ last_name }},<br/>'
                        email_text += form.cleaned_data['email_text']
                        email_text_html += '{{ email_text|linebreaks }}'
                        if form.cleaned_data['include_scipost_summary']:
                            email_text += SCIPOST_SUMMARY_FOOTER
                            email_text_html += SCIPOST_SUMMARY_FOOTER_HTML
                        email_text_html += EMAIL_FOOTER
                        url_unsubscribe = reverse('scipost:unsubscribe',
                                                  args=[member.contributor.id,
                                                        member.contributor.activation_key])
                        email_text += ('\n\nDon\'t want to receive such emails? '
                                       'Unsubscribe by visiting %s.' % url_unsubscribe)
                        email_text_html += (
                            '<br/>\n<p style="font-size: 10px;">Don\'t want to receive such '
                            'emails? <a href="%s">Unsubscribe</a>.</p>' % url_unsubscribe)
                        email_context = {
                            'title': member.contributor.get_title_display(),
                            'last_name': member.last_name,
                            'email_text': form.cleaned_data['email_text'],
                            'key': member.contributor.activation_key,
                        }
                        html_template = Template(email_text_html)
                        html_version = html_template.render(Context(email_context))
                        message = EmailMultiAlternatives(
                            form.cleaned_data['email_subject'],
                            email_text, 'SciPost Admin <admin@scipost.org>',
                            [member.email], connection=connection)
                        message.attach_alternative(html_version, 'text/html')
                        message.send()
        context = {'ack_header': 'The email has been sent.',
                   'followup_message': 'Return to your ',
                   'followup_link': reverse('scipost:personal_page'),
                   'followup_link_label': 'personal page'}
        return render(request, 'scipost/acknowledgement.html', context)

    context = {'form': form}
    return render(request, 'scipost/email_group_members.html', context)


@permission_required('scipost.can_email_particulars', return_403=True)
def email_particular(request):
    """
    Method to send emails to individuals (registered or not)
    """
    if request.method == 'POST':
        form = EmailParticularForm(request.POST)
        if form.is_valid():
            email_text = form.cleaned_data['email_text']
            email_text_html = '{{ email_text|linebreaks }}'
            email_context = {'email_text': form.cleaned_data['email_text']}
            if form.cleaned_data['include_scipost_summary']:
                email_text += SCIPOST_SUMMARY_FOOTER
                email_text_html += SCIPOST_SUMMARY_FOOTER_HTML

            email_text_html += '<br/>' + EMAIL_FOOTER
            html_template = Template(email_text_html)
            html_version = html_template.render(Context(email_context))
            message = EmailMultiAlternatives(
                form.cleaned_data['email_subject'],
                email_text, 'SciPost Admin <admin@scipost.org>',
                [form.cleaned_data['email_address']],
                bcc=['admin@scipost.org'])
            message.attach_alternative(html_version, 'text/html')
            message.send()
            context = {'ack_header': 'The email has been sent.',
                       'followup_message': 'Return to your ',
                       'followup_link': reverse('scipost:personal_page'),
                       'followup_link_label': 'personal page'}
            return render(request, 'scipost/acknowledgement.html', context)
    form = EmailParticularForm()
    context = {'form': form}
    return render(request, 'scipost/email_particular.html', context)


@permission_required('scipost.can_email_particulars', return_403=True)
def send_precooked_email(request):
    """
    Method to send precooked emails to individuals (registered or not)
    """
    form = SendPrecookedEmailForm(request.POST or None)
    if form.is_valid():
        precookedEmail = form.cleaned_data['email_option']
        if form.cleaned_data['email_address'] in precookedEmail.emailed_to:
            errormessage = 'This message has already been sent to this address'
            return render(request, 'scipost/error.html',
                          context={'errormessage': errormessage})
        precookedEmail.emailed_to.append(form.cleaned_data['email_address'])
        precookedEmail.date_last_used = timezone.now().date()
        precookedEmail.save()
        email_text = precookedEmail.email_text
        email_text_html = '{{ email_text|linebreaks }}'
        email_context = {'email_text': precookedEmail.email_text_html}
        if form.cleaned_data['include_scipost_summary']:
            email_text += SCIPOST_SUMMARY_FOOTER
            email_text_html += SCIPOST_SUMMARY_FOOTER_HTML

        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(Context(email_context))
        message = EmailMultiAlternatives(
            precookedEmail.email_subject,
            email_text,
            SciPost_from_addresses_dict[form.cleaned_data['from_address']],
            [form.cleaned_data['email_address']],
            bcc=['admin@scipost.org'])
        message.attach_alternative(html_version, 'text/html')
        message.send()
        context = {'ack_header': 'The email has been sent.',
                   'followup_message': 'Return to your ',
                   'followup_link': reverse('scipost:personal_page'),
                   'followup_link_label': 'personal page'}
        return render(request, 'scipost/acknowledgement.html', context)

    context = {'form': form}
    return render(request, 'scipost/send_precooked_email.html', context)


#####################
# Editorial College #
#####################

def EdCol_bylaws(request):
    return render(request, 'scipost/EdCol_by-laws.html')


@login_required
@fellowship_or_admin_required()
def Fellow_activity_overview(request):
    fellows = (Contributor.objects.fellows()
               .prefetch_related('editorial_assignments')
               .order_by('user__last_name'))
    context = {
        'fellows': fellows
    }

    if request.GET.get('fellow'):
        try:
            fellow = fellows.get(pk=request.GET['fellow'])
            context['fellow'] = fellow

            context['assignments_ongoing'] = (fellow.editorial_assignments
                                              .ongoing()
                                              .get_for_user_in_pool(request.user))
            context['assignments_completed'] = (fellow.editorial_assignments
                                                .completed()
                                                .get_for_user_in_pool(request.user))
        except Contributor.DoesNotExist:
            pass
    return render(request, 'scipost/Fellow_activity_overview.html', context)


class AboutView(ListView):
    """Basic information page with stream of current regular Fellows."""

    model = EditorialCollege
    template_name = 'scipost/about.html'
    queryset = Fellowship.objects.none()

    def get_context_data(self, *args, **kwargs):
        """Save Fellowships per discipline to the context."""
        context = super().get_context_data(*args, **kwargs)
        context['disciplines'] = {}
        for discipline in SCIPOST_DISCIPLINES:
            qs = Fellowship.objects.active().regular().filter(
                contributor__discipline=discipline[0])
            if qs:
                context['disciplines'][discipline[1]] = (qs, subject_areas_raw_dict[discipline[1]])
        return context


def csrf_failure(request, reason=''):
    """CSRF Failure page with an admin mailing action."""
    # Filter out privacy data
    post_data = {}
    for key in request.POST.keys():
        if key:
            post_data[key] = cleanse_setting(key, request.POST[key])

    # Email content
    body = {
        'ERROR': str(reason),
        'USER': str(request.user),
        'GET': dict(request.GET),
        'POST': post_data,
        'META': {k: str(v) for k, v in request.META.items()},
        'COOKIES': {k: str(v) for k, v in request.COOKIES.items()},
    }

    body = json.dumps(body, indent=4)

    mail.mail_admins('CSRF Failure', body)
    return render(request, 'csrf-failure.html')
