from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.contrib.auth.views import password_reset, password_reset_confirm
from django.core import mail
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db.models import Prefetch
from django.http import Http404
from django.shortcuts import redirect
from django.template import Context, Template
from django.views.decorators.http import require_POST
from django.views.generic.list import ListView
from django.views.static import serve

from guardian.decorators import permission_required
from guardian.shortcuts import assign_perm, get_objects_for_user
from haystack.generic_views import SearchView

from .constants import SCIPOST_SUBJECT_AREAS, subject_areas_raw_dict, SciPost_from_addresses_dict
from .decorators import has_contributor
from .models import Contributor, CitationNotification, UnavailabilityPeriod,\
                    DraftInvitation, RegistrationInvitation,\
                    AuthorshipClaim, EditorialCollege, EditorialCollegeFellowship
from .forms import AuthenticationForm, DraftInvitationForm, UnavailabilityPeriodForm,\
                   RegistrationForm, RegistrationInvitationForm, AuthorshipClaimForm,\
                   ModifyPersonalMessageForm, SearchForm, VetRegistrationForm, reg_ref_dict,\
                   UpdatePersonalDataForm, UpdateUserDataForm, PasswordChangeForm,\
                   EmailGroupMembersForm, EmailParticularForm, SendPrecookedEmailForm
from .utils import Utils, EMAIL_FOOTER, SCIPOST_SUMMARY_FOOTER, SCIPOST_SUMMARY_FOOTER_HTML

from commentaries.models import Commentary
from comments.models import Comment
from journals.models import Publication, Journal
from news.models import NewsItem
from submissions.models import Submission, EditorialAssignment, RefereeInvitation,\
                               Report, EICRecommendation
from partners.models import MembershipAgreement
from theses.models import ThesisLink


##############
# Utilitites #
##############

def is_registered(user):
    """
    This method checks if user is activated assuming an validated user
    has at least one permission group (`Registered Contributor` or `Partner Accounts`).
    """
    return user.groups.exists()


class SearchView(SearchView):
    template_name = 'search/search.html'
    form_class = SearchForm

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['search_query'] = self.request.GET.get('q')
        ctx['results_count'] = kwargs['object_list'].count()

        # Methods not supported by Whoosh engine
        # ctx['stats_results'] = kwargs['object_list'].stats_results()
        # ctx['facet_counts'] = kwargs['object_list'].facet('text').facet_counts()
        return ctx


#############
# Main view
#############

def index(request):
    '''Main page.'''
    context = {
        'latest_newsitem': NewsItem.objects.filter(on_homepage=True).order_by('-date').first(),
        'submissions': Submission.objects.public().order_by('-submission_date')[:3],
        'journals': Journal.objects.order_by('name'),
        'publications': Publication.objects.published().order_by('-publication_date',
                                                                 '-paper_nr')[:3],
        'current_agreements': MembershipAgreement.objects.now_active()[:2],
    }
    return render(request, 'scipost/index.html', context)


def protected_serve(request, path, show_indexes=False):
    """
    Serve files that are saved outside the default MEDIA_ROOT folder for superusers only!
    This will be usefull eg. in the admin pages.
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
    context = {'subject_areas_physics': SCIPOST_SUBJECT_AREAS[0][1]}
    return render(request, 'scipost/feeds.html', context)


################
# Contributors:
################

def register(request):
    """
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
        Utils.load({'contributor': contributor}, request)
        Utils.send_registration_email()

        # Disable invitations related to the new Contributor
        (RegistrationInvitation.objects.filter(email=form.cleaned_data['email'])
         .update(responded=True))

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
    """
    If a scientist has recieved an invitation (RegistrationInvitation)
    he/she will finish it's invitation via still view which will prefill
    the default registration form.
    """
    invitation = get_object_or_404(RegistrationInvitation, invitation_key=key)
    if invitation.responded:
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
        context = {'ack_header': 'Your email address has been confirmed.',
                   'ack_message': ('Your SciPost account will soon be vetted. '
                                   'You will soon receive an email from us.'),
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
        Utils.load({'contributor': contributor}, request)
        Utils.send_new_activation_link_email()

        context = {
            'ack_header': 'We have emailed you a new activation link.',
            'ack_message': ('Please acknowledge it within its 48 hours validity '
                            'window if you want us to proceed with vetting your registraion.'),
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
    contributors_to_vet = (Contributor.objects
                           .filter(user__is_active=True, status=0)
                           .order_by('key_expires'))
    form = VetRegistrationForm()
    context = {'contributors_to_vet': contributors_to_vet, 'form': form}
    return render(request, 'scipost/vet_registration_requests.html', context)


@permission_required('scipost.can_vet_registration_requests', return_403=True)
def vet_registration_request_ack(request, contributor_id):
    # process the form
    form = VetRegistrationForm(request.POST or None)
    contributor = Contributor.objects.get(pk=contributor_id)
    if form.is_valid():
        if form.promote_to_registered_contributor():
            contributor.status = 1
            contributor.vetted_by = request.user.contributor
            contributor.save()
            group = Group.objects.get(name='Registered Contributors')
            contributor.user.groups.add(group)
            # Verify if there is a pending refereeing invitation
            pending_ref_inv_exists = True
            try:
                pending_ref_inv = RefereeInvitation.objects.get(
                    invitation_key=contributor.invitation_key, cancelled=False)
                pending_ref_inv.referee = contributor
                pending_ref_inv.save()
            except RefereeInvitation.DoesNotExist:
                pending_ref_inv_exists = False

            email_text = ('Dear ' + contributor.get_title_display() + ' '
                          + contributor.user.last_name +
                          ', \n\nYour registration to the SciPost publication portal '
                          'has been accepted. '
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
            ref_reason = int(form.cleaned_data['refusal_reason'])
            email_text = ('Dear ' + contributor.get_title_display() + ' '
                          + contributor.user.last_name +
                          ', \n\nYour registration to the SciPost publication portal '
                          'has been turned down, the reason being: '
                          + reg_ref_dict[ref_reason] + '. You can however still view '
                          'all SciPost contents, just not submit papers, '
                          'comments or votes. We nonetheless thank you for your interest.'
                          '\n\nThe SciPost Team.')
            if form.cleaned_data['email_response_field']:
                email_text += ('\n\nFurther explanations: '
                               + form.cleaned_data['email_response_field'])
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
    unactive_contributors = (Contributor.objects.awaiting_validation()
                             .prefetch_related('user')
                             .order_by('-key_expires'))
    context = {
        'unactive_contributors': unactive_contributors,
        'now': timezone.now()
    }
    return render(request, 'scipost/registration_requests.html', context)


@require_POST
@permission_required('scipost.can_resend_registration_requests', return_403=True)
def registration_requests_reset(request, contributor_id):
    '''
    Reset specific activation_key for Contributor and resend activation mail.
    '''
    contributor = get_object_or_404(Contributor.objects.awaiting_validation(), id=contributor_id)
    contributor.generate_key()
    contributor.save()
    Utils.load({'contributor': contributor}, request)
    Utils.send_new_activation_link_email()
    messages.success(request, ('New key successfully generated and sent to <i>%s</i>'
                               % contributor.user.email))
    return redirect(reverse('scipost:registration_requests'))


@permission_required('scipost.can_draft_registration_invitations', return_403=True)
def draft_registration_invitation(request):
    """
    For officers to prefill registration invitations.
    This is similar to the registration_invitations method,
    which is used to complete the invitation process.
    """
    draft_inv_form = DraftInvitationForm(request.POST or None, current_user=request.user)
    if draft_inv_form.is_valid():
        invitation = draft_inv_form.save(commit=False)
        invitation.drafted_by = request.user.contributor
        invitation.save()

        # Assign permission to 'drafter' to edit the draft afterwards
        assign_perm('comments.change_draftinvitation', request.user, invitation)
        messages.success(request, 'Draft invitation saved.')
        return redirect(reverse('scipost:draft_registration_invitation'))

    sent_reg_inv = RegistrationInvitation.objects.filter(responded=False, declined=False)
    sent_reg_inv_fellows = sent_reg_inv.filter(invitation_type='F').order_by('last_name')
    sent_reg_inv_contrib = sent_reg_inv.filter(invitation_type='C').order_by('last_name')
    sent_reg_inv_ref = sent_reg_inv.filter(invitation_type='R').order_by('last_name')
    sent_reg_inv_cited_sub = sent_reg_inv.filter(invitation_type='ci').order_by('last_name')
    sent_reg_inv_cited_pub = sent_reg_inv.filter(invitation_type='cp').order_by('last_name')

    resp_reg_inv = RegistrationInvitation.objects.filter(responded=True, declined=False)
    resp_reg_inv_fellows = resp_reg_inv.filter(invitation_type='F').order_by('last_name')
    resp_reg_inv_contrib = resp_reg_inv.filter(invitation_type='C').order_by('last_name')
    resp_reg_inv_ref = resp_reg_inv.filter(invitation_type='R').order_by('last_name')
    resp_reg_inv_cited_sub = resp_reg_inv.filter(invitation_type='ci').order_by('last_name')
    resp_reg_inv_cited_pub = resp_reg_inv.filter(invitation_type='cp').order_by('last_name')

    decl_reg_inv = RegistrationInvitation.objects.filter(
        responded=True, declined=True).order_by('last_name')

    names_reg_contributors = (Contributor.objects.filter(status=1).order_by('user__last_name')
                              .values_list('user__first_name', 'user__last_name'))
    existing_drafts = DraftInvitation.objects.filter(processed=False).order_by('last_name')

    context = {
        'draft_inv_form': draft_inv_form,
        'sent_reg_inv_fellows': sent_reg_inv_fellows,
        'sent_reg_inv_contrib': sent_reg_inv_contrib,
        'sent_reg_inv_ref': sent_reg_inv_ref,
        'sent_reg_inv_cited_sub': sent_reg_inv_cited_sub,
        'sent_reg_inv_cited_pub': sent_reg_inv_cited_pub,
        'resp_reg_inv_fellows': resp_reg_inv_fellows,
        'resp_reg_inv_contrib': resp_reg_inv_contrib,
        'resp_reg_inv_ref': resp_reg_inv_ref,
        'resp_reg_inv_cited_sub': resp_reg_inv_cited_sub,
        'resp_reg_inv_cited_pub': resp_reg_inv_cited_pub,
        'decl_reg_inv': decl_reg_inv,
        'names_reg_contributors': names_reg_contributors,
        'existing_drafts': existing_drafts,
    }
    return render(request, 'scipost/draft_registration_invitation.html', context)


@login_required
def edit_draft_reg_inv(request, draft_id):
    draft = get_object_or_404((get_objects_for_user(request.user, 'scipost.change_draftinvitation')
                               .filter(processed=False)),
                              id=draft_id)

    draft_inv_form = DraftInvitationForm(request.POST or None, current_user=request.user,
                                         instance=draft)
    if draft_inv_form.is_valid():
        draft = draft_inv_form.save()
        messages.success(request, 'Draft invitation saved.')
        return redirect(reverse('scipost:registration_invitations'))

    context = {'draft_inv_form': draft_inv_form}
    return render(request, 'scipost/edit_draft_reg_inv.html', context)


@permission_required('scipost.can_manage_registration_invitations', return_403=True)
def map_draft_reg_inv_to_contributor(request, draft_id, contributor_id):
    """
    If a draft invitation actually points to an already-registered
    Contributor, this method marks the draft invitation as processed
    and, if the draft invitation was for a citation type,
    creates an instance of CitationNotification.
    """
    draft = get_object_or_404(DraftInvitation, id=draft_id)
    contributor = get_object_or_404(Contributor, id=contributor_id)
    draft.processed = True
    draft.save()
    citation = CitationNotification(
        contributor=contributor,
        cited_in_submission=draft.cited_in_submission,
        cited_in_publication=draft.cited_in_publication,
        processed=False)
    citation.save()
    return redirect(reverse('scipost:registration_invitations'))


@permission_required('scipost.can_manage_registration_invitations', return_403=True)
def registration_invitations(request, draft_id=None):
    """ Overview and tools for administrators """
    # List invitations sent; send new ones
    associated_contributors = None
    initial = {}
    if draft_id:
        # Fill draft data if draft_id given
        draft = get_object_or_404(DraftInvitation, id=draft_id)
        associated_contributors = Contributor.objects.filter(
            user__last_name__icontains=draft.last_name)
        initial = {
            'title': draft.title,
            'first_name': draft.first_name,
            'last_name': draft.last_name,
            'email': draft.email,
            'invitation_type': draft.invitation_type,
            'cited_in_submission': draft.cited_in_submission,
            'cited_in_publication': draft.cited_in_publication,
        }

    # Send invitation from form information
    reg_inv_form = RegistrationInvitationForm(request.POST or None, initial=initial,
                                              current_user=request.user)
    if reg_inv_form.is_valid():
        invitation = reg_inv_form.save(commit=False)
        invitation.invited_by = request.user.contributor
        invitation.save()

        Utils.load({'invitation': invitation})
        Utils.send_registration_invitation_email()
        (DraftInvitation.objects.filter(email=reg_inv_form.cleaned_data['email'])
         .update(processed=True))

        messages.success(request, 'Registration Invitation sent')
        return redirect(reverse('scipost:registration_invitations'))

    sent_reg_inv = RegistrationInvitation.objects.filter(responded=False, declined=False)
    sent_reg_inv_fellows = sent_reg_inv.filter(invitation_type='F').order_by('last_name')
    sent_reg_inv_contrib = sent_reg_inv.filter(invitation_type='C').order_by('last_name')
    sent_reg_inv_ref = sent_reg_inv.filter(invitation_type='R').order_by('last_name')
    sent_reg_inv_cited_sub = sent_reg_inv.filter(invitation_type='ci').order_by('last_name')
    sent_reg_inv_cited_pub = sent_reg_inv.filter(invitation_type='cp').order_by('last_name')

    resp_reg_inv = RegistrationInvitation.objects.filter(responded=True, declined=False)
    resp_reg_inv_fellows = resp_reg_inv.filter(invitation_type='F').order_by('last_name')
    resp_reg_inv_contrib = resp_reg_inv.filter(invitation_type='C').order_by('last_name')
    resp_reg_inv_ref = resp_reg_inv.filter(invitation_type='R').order_by('last_name')
    resp_reg_inv_cited_sub = resp_reg_inv.filter(invitation_type='ci').order_by('last_name')
    resp_reg_inv_cited_pub = resp_reg_inv.filter(invitation_type='cp').order_by('last_name')

    decl_reg_inv = RegistrationInvitation.objects.filter(responded=True, declined=True)

    names_reg_contributors = Contributor.objects.filter(
        status=1).order_by('user__last_name').values_list(
        'user__first_name', 'user__last_name')
    existing_drafts = DraftInvitation.objects.filter(processed=False).order_by('last_name')

    context = {
        'reg_inv_form': reg_inv_form,
        'sent_reg_inv_fellows': sent_reg_inv_fellows,
        'sent_reg_inv_contrib': sent_reg_inv_contrib,
        'sent_reg_inv_ref': sent_reg_inv_ref,
        'sent_reg_inv_cited_sub': sent_reg_inv_cited_sub,
        'sent_reg_inv_cited_pub': sent_reg_inv_cited_pub,
        'resp_reg_inv_fellows': resp_reg_inv_fellows,
        'resp_reg_inv_contrib': resp_reg_inv_contrib,
        'resp_reg_inv_ref': resp_reg_inv_ref,
        'resp_reg_inv_cited_sub': resp_reg_inv_cited_sub,
        'resp_reg_inv_cited_pub': resp_reg_inv_cited_pub,
        'decl_reg_inv': decl_reg_inv,
        'names_reg_contributors': names_reg_contributors,
        'existing_drafts': existing_drafts,
        'associated_contributors': associated_contributors,
    }
    return render(request, 'scipost/registration_invitations.html', context)


@permission_required('scipost.can_manage_registration_invitations', return_403=True)
def registration_invitations_cleanup(request):
    """
    Compares the email addresses of invitations with those in the
    database of registered Contributors. Flags overlaps.
    """
    contributor_email_list = Contributor.objects.values_list('user__email', flat=True)
    invs_to_cleanup = RegistrationInvitation.objects.filter(
        responded=False, email__in=contributor_email_list)
    context = {'invs_to_cleanup': invs_to_cleanup}
    return render(request, 'scipost/registration_invitations_cleanup.html', context)


@permission_required('scipost.can_manage_registration_invitations', return_403=True)
def remove_registration_invitation(request, invitation_id):
    """
    Remove an invitation (called from registration_invitations_cleanup).
    """
    invitation = get_object_or_404(RegistrationInvitation, pk=invitation_id)
    invitation.delete()
    return redirect(reverse('scipost:registration_invitations_cleanup'))


@permission_required('scipost.can_manage_registration_invitations', return_403=True)
def edit_invitation_personal_message(request, invitation_id):
    """

    DOES THIS THING STILL WORK? OR CAN IT BE REMOVED?

    -- JdW (August 14th, 2017)

    """
    invitation = get_object_or_404(RegistrationInvitation, pk=invitation_id)
    errormessage = None
    if request.method == 'POST':
        form = ModifyPersonalMessageForm(request.POST)
        if form.is_valid():
            invitation.personal_message = form.cleaned_data['personal_message']
            invitation.save()
            return redirect(reverse('scipost:registration_invitations'))
        else:
            errormessage = 'The form was invalid.'
    else:
        form = ModifyPersonalMessageForm(
            initial={'personal_message': invitation.personal_message, })
    context = {'invitation': invitation,
               'form': form, 'errormessage': errormessage, }
    return render(request, 'scipost/edit_invitation_personal_message.html', context)


@permission_required('scipost.can_manage_registration_invitations', return_403=True)
def renew_registration_invitation(request, invitation_id):
    """
    Renew an invitation (called from registration_invitations).
    """
    invitation = get_object_or_404(RegistrationInvitation, pk=invitation_id)
    errormessage = None
    if(invitation.invitation_type == 'F'
       and not request.user.has_perm('scipost.can_invite_Fellows')):
        errormessage = ('You do not have the authorization to send a Fellow-type '
                        'invitation. Consider Contributor, or cited (sub/pub). ')
    elif invitation.invitation_type == 'R':
        errormessage = ('Referee-type invitations must be made by the Editor-in-charge '
                        'at the relevant Submission\'s Editorial Page. ')
    if errormessage is not None:
        return render(request, 'scipost/error.html', context={'errormessage': errormessage})

    Utils.load({'invitation': invitation})
    Utils.send_registration_invitation_email(True)
    return redirect(reverse('scipost:registration_invitations'))


@permission_required('scipost.can_manage_registration_invitations', return_403=True)
def mark_reg_inv_as_declined(request, invitation_id):
    """
    Mark an invitation as declined (called from registration_invitations.html).
    """
    invitation = get_object_or_404(RegistrationInvitation, pk=invitation_id)
    invitation.responded = True
    invitation.declined = True
    invitation.save()
    return redirect(reverse('scipost:registration_invitations'))


@permission_required('scipost.can_manage_registration_invitations', return_403=True)
def citation_notifications(request):
    unprocessed_notifications = CitationNotification.objects.filter(
        processed=False).order_by('contributor__user__last_name')
    context = {'unprocessed_notifications': unprocessed_notifications, }
    return render(request, 'scipost/citation_notifications.html', context)


@permission_required('scipost.can_manage_registration_invitations', return_403=True)
def process_citation_notification(request, cn_id):
    notification = get_object_or_404(CitationNotification, id=cn_id)
    notification.processed = True
    notification.save()
    if notification.contributor.accepts_SciPost_emails:
        Utils.load({'notification': notification})
        Utils.send_citation_notification_email()
    return redirect(reverse('scipost:citation_notifications'))


@permission_required('scipost.can_manage_registration_invitations', return_403=True)
def mark_draft_inv_as_processed(request, draft_id):
    draft = get_object_or_404(DraftInvitation, id=draft_id)
    draft.processed = True
    draft.save()
    return redirect(reverse('scipost:registration_invitations'))


def login_view(request):
    """
    This view shows and processes a user's login session.

    The function based method login() is deprecated from
    Django 1.11 and replaced by Class Based Views.

    See:
    https://docs.djangoproject.com/en/1.11/releases/1.11/#django-contrib-auth
    """
    form = AuthenticationForm(request.POST or None, initial=request.GET)
    if form.is_valid():
        user = form.authenticate()
        if user is not None:
            if is_registered(user):
                # This check seems redundant, however do not remove.
                if user.is_active:
                    login(request, user)
                    redirect_to = form.get_redirect_url(request)
                    return redirect(redirect_to)
                else:
                    form.add_error(None, 'Your account is disabled.')
            else:
                form.add_error(None, ('Your account has not yet been vetted. '
                                      '(our admins will verify your credentials very soon)'))
        else:
            form.add_error(None, 'Invalid username/password.')
    context = {'form': form}
    return render(request, 'scipost/login.html', context)


def logout_view(request):
    """
    The function based method logout() is deprecated from
    Django 1.11 and replaced by Class Based Views.

    See:
    https://docs.djangoproject.com/en/1.11/releases/1.11/#django-contrib-auth
    """
    logout(request)
    messages.success(request, ('<h3>Keep contributing!</h3>'
                               'You are now logged out of SciPost.'))
    return redirect(reverse('scipost:index'))


@login_required
@user_passes_test(has_contributor)
def mark_unavailable_period(request):
    '''
    Mark period unavailable for Contributor using this view.
    '''
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
@user_passes_test(has_contributor)
def delete_unavailable_period(request, period_id):
    '''
    Delete period unavailable registered.
    '''
    unav = get_object_or_404(UnavailabilityPeriod,
                             contributor=request.user.contributor, id=int(period_id))
    unav.delete()
    messages.success(request, 'Unavailability period deleted')
    return redirect('scipost:personal_page')


@login_required
@user_passes_test(has_contributor)
def personal_page(request):
    """
    The Personal Page is the main view for accessing user functions.
    """
    contributor = Contributor.objects.select_related('user').get(user=request.user)
    user_groups = contributor.user.groups.values_list('name', flat=True)

    # Compile the unavailability periods:
    now = timezone.now()
    unavailabilities = UnavailabilityPeriod.objects.filter(
        contributor=contributor).exclude(end__lt=now).order_by('start')
    unavailability_form = UnavailabilityPeriodForm()

    # if an editor, count the number of actions required:
    nr_reg_to_vet = 0
    nr_reg_awaiting_validation = 0
    nr_submissions_to_assign = 0
    nr_recommendations_to_prepare_for_voting = 0
    if contributor.is_SP_Admin():
        # count the number of pending registration requests
        nr_reg_to_vet = Contributor.objects.filter(user__is_active=True, status=0).count()
        nr_reg_awaiting_validation = (Contributor.objects.awaiting_validation()
                                    #   .filter(key_expires__gte=now, key_expires__lte=intwodays)
                                      .count())
        nr_submissions_to_assign = Submission.objects.filter(status__in=['unassigned']).count()
        nr_recommendations_to_prepare_for_voting = EICRecommendation.objects.filter(
            submission__status__in=['voting_in_preparation']).count()

    nr_assignments_to_consider = 0
    active_assignments = None
    nr_reports_to_vet = 0
    if contributor.is_MEC():
        nr_assignments_to_consider = (EditorialAssignment.objects
                                      .filter(to=contributor, accepted=None, deprecated=False)
                                      .count())
        active_assignments = EditorialAssignment.objects.filter(
            to=contributor, accepted=True, completed=False)
        nr_reports_to_vet = (Report.objects.awaiting_vetting()
                             .filter(submission__editor_in_charge=contributor).count())
    nr_commentary_page_requests_to_vet = 0
    nr_comments_to_vet = 0
    nr_thesislink_requests_to_vet = 0
    nr_authorship_claims_to_vet = 0
    if contributor.is_VE():
        nr_commentary_page_requests_to_vet = (Commentary.objects.awaiting_vetting()
                                              .exclude(requested_by=contributor).count())
        nr_comments_to_vet = Comment.objects.awaiting_vetting().count()
        nr_thesislink_requests_to_vet = ThesisLink.objects.filter(vetted=False).count()
        nr_authorship_claims_to_vet = AuthorshipClaim.objects.filter(status='0').count()

    # Refereeing
    nr_ref_inv_to_consider = RefereeInvitation.objects.filter(
        referee=contributor, accepted=None, cancelled=False).count()
    pending_ref_tasks = RefereeInvitation.objects.filter(
        referee=contributor, accepted=True, fulfilled=False)
    refereeing_tab_total_count = nr_ref_inv_to_consider + len(pending_ref_tasks)
    refereeing_tab_total_count += Report.objects.in_draft().filter(author=contributor).count()

    # Verify if there exist objects authored by this contributor,
    # whose authorship hasn't been claimed yet
    own_publications = (Publication.objects
                       .filter(authors__in=[contributor])
                       .order_by('-publication_date'))
    own_submissions = (Submission.objects
                       .filter(authors__in=[contributor], is_current=True)
                       .order_by('-submission_date'))
    own_commentaries = Commentary.objects.filter(authors=contributor).order_by('-latest_activity')
    own_thesislinks = ThesisLink.objects.filter(author_as_cont__in=[contributor])
    nr_publication_authorships_to_claim = (Publication.objects.filter(
        author_list__contains=contributor.user.last_name)
                                          .exclude(authors__in=[contributor])
                                          .exclude(authors_claims__in=[contributor])
                                          .exclude(authors_false_claims__in=[contributor])
                                          .count())
    nr_submission_authorships_to_claim = (Submission.objects.filter(
        author_list__contains=contributor.user.last_name)
                                          .exclude(authors__in=[contributor])
                                          .exclude(authors_claims__in=[contributor])
                                          .exclude(authors_false_claims__in=[contributor])
                                          .count())
    nr_commentary_authorships_to_claim = (Commentary.objects.filter(
        author_list__contains=contributor.user.last_name)
                                          .exclude(authors__in=[contributor])
                                          .exclude(authors_claims__in=[contributor])
                                          .exclude(authors_false_claims__in=[contributor])
                                          .count())
    nr_thesis_authorships_to_claim = (ThesisLink.objects.filter(
        author__contains=contributor.user.last_name)
                                      .exclude(author_as_cont__in=[contributor])
                                      .exclude(author_claims__in=[contributor])
                                      .exclude(author_false_claims__in=[contributor])
                                      .count())
    own_comments = (Comment.objects.filter(author=contributor, is_author_reply=False)
                    .select_related('author', 'submission')
                    .order_by('-date_submitted'))
    own_authorreplies = (Comment.objects.filter(author=contributor, is_author_reply=True)
                         .order_by('-date_submitted'))

    appellation = contributor.get_title_display() + ' ' + contributor.user.last_name
    context = {
        'contributor': contributor,
        'user_groups': user_groups,
        'appellation': appellation,
        'unavailabilities': unavailabilities,
        'unavailability_form': unavailability_form,
        'nr_reg_to_vet': nr_reg_to_vet,
        'nr_reg_awaiting_validation': nr_reg_awaiting_validation,
        'nr_commentary_page_requests_to_vet': nr_commentary_page_requests_to_vet,
        'nr_comments_to_vet': nr_comments_to_vet,
        'nr_thesislink_requests_to_vet': nr_thesislink_requests_to_vet,
        'nr_authorship_claims_to_vet': nr_authorship_claims_to_vet,
        'nr_reports_to_vet': nr_reports_to_vet,
        'nr_submissions_to_assign': nr_submissions_to_assign,
        'nr_recommendations_to_prepare_for_voting': nr_recommendations_to_prepare_for_voting,
        'nr_assignments_to_consider': nr_assignments_to_consider,
        'active_assignments': active_assignments,
        'nr_publication_authorships_to_claim': nr_publication_authorships_to_claim,
        'nr_submission_authorships_to_claim': nr_submission_authorships_to_claim,
        'nr_commentary_authorships_to_claim': nr_commentary_authorships_to_claim,
        'nr_thesis_authorships_to_claim': nr_thesis_authorships_to_claim,
        'nr_ref_inv_to_consider': nr_ref_inv_to_consider,
        'pending_ref_tasks': pending_ref_tasks,
        'refereeing_tab_total_count': refereeing_tab_total_count,
        'own_publications': own_publications,
        'own_submissions': own_submissions,
        'own_commentaries': own_commentaries,
        'own_thesislinks': own_thesislinks,
        'own_comments': own_comments,
        'own_authorreplies': own_authorreplies,
    }

    # Only add variables if user has right permission
    if request.user.has_perm('scipost.can_manage_reports'):
        context['nr_reports_without_pdf'] = (Report.objects.accepted()
                                             .filter(pdf_report='').count())
        context['nr_treated_submissions_without_pdf'] = (Submission.objects.treated()
                                                         .filter(pdf_refereeing_pack='').count())

    return render(request, 'scipost/personal_page.html', context)


@login_required
def change_password(request):
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
            return redirect(reverse('partners:dashboard'))
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
        return redirect(reverse('partners:dashboard'))
    context = {
        'user_form': user_form
    }
    return render(request, 'scipost/update_personal_data.html', context)


def _update_personal_data_contributor(request):
    contributor = Contributor.objects.get(user=request.user)
    user_form = UpdateUserDataForm(request.POST or None, instance=request.user)
    cont_form = UpdatePersonalDataForm(request.POST or None, instance=contributor)
    if user_form.is_valid() and cont_form.is_valid():
        user_form.save()
        cont_form.save()
        cont_form.sync_lists()
        if 'orcid_id' in cont_form.changed_data:
            cont_form.propagate_orcid()
        messages.success(request, 'Your personal data has been updated.')
        return redirect(reverse('scipost:personal_page'))
    else:
        user_form = UpdateUserDataForm(instance=contributor.user)
        cont_form = UpdatePersonalDataForm(instance=contributor)
    return render(request, 'scipost/update_personal_data.html',
                  {'user_form': user_form, 'cont_form': cont_form})


@login_required
def update_personal_data(request):
    if has_contributor(request.user):
        return _update_personal_data_contributor(request)
    return _update_personal_data_user_only(request)


@login_required
@user_passes_test(has_contributor)
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
                                       .exclude(authors__in=[contributor])
                                       .exclude(authors_claims__in=[contributor])
                                       .exclude(authors_false_claims__in=[contributor]))
    pub_auth_claim_form = AuthorshipClaimForm()
    submission_authorships_to_claim = (Submission.objects
                                       .filter(author_list__contains=contributor.user.last_name)
                                       .exclude(authors__in=[contributor])
                                       .exclude(authors_claims__in=[contributor])
                                       .exclude(authors_false_claims__in=[contributor]))
    sub_auth_claim_form = AuthorshipClaimForm()
    commentary_authorships_to_claim = (Commentary.objects
                                       .filter(author_list__contains=contributor.user.last_name)
                                       .exclude(authors__in=[contributor])
                                       .exclude(authors_claims__in=[contributor])
                                       .exclude(authors_false_claims__in=[contributor]))
    com_auth_claim_form = AuthorshipClaimForm()
    thesis_authorships_to_claim = (ThesisLink.objects
                                   .filter(author__contains=contributor.user.last_name)
                                   .exclude(author_as_cont__in=[contributor])
                                   .exclude(author_claims__in=[contributor])
                                   .exclude(author_false_claims__in=[contributor]))
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
@user_passes_test(has_contributor)
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
@user_passes_test(has_contributor)
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
@user_passes_test(has_contributor)
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
@user_passes_test(has_contributor)
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

        if claim_to_vet.publication is not None:
            claim_to_vet.publication.authors_claims.remove(claim_to_vet.claimant)
            if claim == '1':
                claim_to_vet.publication.authors.add(claim_to_vet.claimant)
                claim_to_vet.status = '1'
            elif claim == '0':
                claim_to_vet.publication.authors_false_claims.add(claim_to_vet.claimant)
                claim_to_vet.status = '-1'
            claim_to_vet.publication.save()
        if claim_to_vet.submission is not None:
            claim_to_vet.submission.authors_claims.remove(claim_to_vet.claimant)
            if claim == '1':
                claim_to_vet.submission.authors.add(claim_to_vet.claimant)
                claim_to_vet.status = '1'
            elif claim == '0':
                claim_to_vet.submission.authors_false_claims.add(claim_to_vet.claimant)
                claim_to_vet.status = '-1'
            claim_to_vet.submission.save()
        if claim_to_vet.commentary is not None:
            claim_to_vet.commentary.authors_claims.remove(claim_to_vet.claimant)
            if claim == '1':
                claim_to_vet.commentary.authors.add(claim_to_vet.claimant)
                claim_to_vet.status = '1'
            elif claim == '0':
                claim_to_vet.commentary.authors_false_claims.add(claim_to_vet.claimant)
                claim_to_vet.status = '-1'
            claim_to_vet.commentary.save()
        if claim_to_vet.thesislink is not None:
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
    contributor_publications = Publication.objects.published().filter(authors=contributor)
    contributor_submissions = Submission.objects.public_unlisted().filter(authors=contributor)
    contributor_commentaries = Commentary.objects.filter(authors=contributor)
    contributor_theses = ThesisLink.objects.vetted().filter(author_as_cont=contributor)
    contributor_comments = (Comment.objects.vetted()
                            .filter(author=contributor, is_author_reply=False)
                            .order_by('-date_submitted'))
    contributor_authorreplies = (Comment.objects.vetted()
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


@permission_required('scipost.can_view_pool', return_403=True)
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
    model = EditorialCollege
    template_name = 'scipost/about.html'
    queryset = EditorialCollege.objects.prefetch_related(
                Prefetch('fellowships',
                         queryset=EditorialCollegeFellowship.objects.active().select_related(
                            'contributor__user').order_by('contributor__user__last_name'),
                         to_attr='current_fellows'))

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        object_list = []
        for college in context['object_list']:
            try:
                spec_list = subject_areas_raw_dict[str(college)]
            except KeyError:
                spec_list = None
            object_list.append((
                college,
                spec_list,
            ))
        context['object_list'] = object_list
        return context
