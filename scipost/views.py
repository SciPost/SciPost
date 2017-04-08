import datetime
import hashlib
import random
import re
import string

from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth.views import password_reset, password_reset_confirm
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core import mail
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.template import Context, Template
from django.utils.http import is_safe_url
from django.views.generic.list import ListView

from django.db.models import Prefetch

from guardian.decorators import permission_required

from .constants import SCIPOST_SUBJECT_AREAS, subject_areas_raw_dict, SciPost_from_addresses_dict
from .models import Contributor, CitationNotification, UnavailabilityPeriod,\
                    DraftInvitation, RegistrationInvitation,\
                    AuthorshipClaim, SupportingPartner, SPBMembershipAgreement,\
                    EditorialCollege, EditorialCollegeFellowship
from .forms import AuthenticationForm, DraftInvitationForm, UnavailabilityPeriodForm,\
                   RegistrationForm, RegistrationInvitationForm, AuthorshipClaimForm,\
                   ModifyPersonalMessageForm, SearchForm, VetRegistrationForm, reg_ref_dict,\
                   UpdatePersonalDataForm, UpdateUserDataForm, PasswordChangeForm,\
                   EmailGroupMembersForm, EmailParticularForm, SendPrecookedEmailForm,\
                   SupportingPartnerForm, SPBMembershipForm
from .utils import Utils, EMAIL_FOOTER, SCIPOST_SUMMARY_FOOTER, SCIPOST_SUMMARY_FOOTER_HTML

from commentaries.models import Commentary
from comments.models import Comment
from journals.models import Publication, Issue
from news.models import NewsItem
from submissions.constants import SUBMISSION_STATUS_PUBLICLY_UNLISTED
from submissions.models import Submission, EditorialAssignment, RefereeInvitation,\
                               Report, EICRecommendation
from theses.models import ThesisLink


##############
# Utilitites #
##############

def is_registered(user):
    return user.groups.filter(name='Registered Contributors').exists()


def is_SP_Admin(user):
    return user.groups.filter(name='SciPost Administrators').exists()


def is_MEC(user):
    return user.groups.filter(name='Editorial College').exists()


def is_VE(user):
    return user.groups.filter(name='Vetting Editors').exists()


# Global search

def normalize_query(query_string,
                    findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                    normspace=re.compile(r'\s{2,}').sub):
    """ Splits a query string in individual keywords, keeping quoted words together. """
    return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)]


def get_query(query_string, search_fields):
    """ Returns a query, namely a combination of Q objects. """
    query = None
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None
        for field_name in search_fields:
            q = Q(**{"%s__icontains" % field_name: term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query & or_query
    return query


def documentsSearchResults(query):
    """
    Searches through commentaries, submissions and thesislinks.
    Returns a Context object which can be further used in templates.
    Naive implementation based on exact match of query.
    NEEDS UPDATING with e.g. Haystack.
    """
    publication_query = get_query(query,
                                  ['title', 'author_list', 'abstract', 'doi_string'])
    commentary_query = get_query(query,
                                 ['pub_title', 'author_list', 'pub_abstract'])
    submission_query = get_query(query,
                                 ['title', 'author_list', 'abstract'])
    thesislink_query = get_query(query,
                                 ['title', 'author', 'abstract', 'supervisor'])
    comment_query = get_query(query,
                              ['comment_text'])

    publication_search_queryset = Publication.objects.filter(
        publication_query,
        ).order_by('-publication_date')
    commentary_search_queryset = Commentary.objects.filter(
        commentary_query,
        vetted=True,
        ).order_by('-pub_date')
    submission_search_queryset = Submission.objects.filter(
        submission_query,
        ).exclude(status__in=SUBMISSION_STATUS_PUBLICLY_UNLISTED,
        ).order_by('-submission_date')
    thesislink_search_list = ThesisLink.objects.filter(
        thesislink_query,
        vetted=True,
        ).order_by('-defense_date')
    comment_search_list = Comment.objects.filter(
        comment_query,
        status__gte='1',
        ).order_by('-date_submitted')
    context = {'publication_search_queryset': publication_search_queryset,
               'commentary_search_queryset': commentary_search_queryset,
               'submission_search_queryset': submission_search_queryset,
               'thesislink_search_list': thesislink_search_list,
               'comment_search_list': comment_search_list}
    return context


def search(request):
    """ For the global search form in navbar """
    form = SearchForm(request.GET or None)
    context = {}
    if form.is_valid():
        context = documentsSearchResults(form.cleaned_data['q'])
        request.session['query'] = form.cleaned_data['q']
        context['search_term'] = form.cleaned_data['q']
    elif 'query' in request.session:
        context = documentsSearchResults(request.session['query'])
        context['search_term'] = request.session['query']

    if 'publication_search_queryset' in context:
        publication_search_list_paginator = Paginator(context['publication_search_queryset'], 10)
        publication_search_list_page = request.GET.get('publication_search_list_page')
        try:
            publication_search_list = publication_search_list_paginator.page(
                publication_search_list_page)
        except PageNotAnInteger:
            publication_search_list = publication_search_list_paginator.page(1)
        except EmptyPage:
            publication_search_list = publication_search_list_paginator.page(
                publication_search_list_paginator.num_pages)
        context['publication_search_list'] = publication_search_list

    if 'commentary_search_queryset' in context:
        commentary_search_list_paginator = Paginator(context['commentary_search_queryset'], 10)
        commentary_search_list_page = request.GET.get('commentary_search_list_page')
        try:
            commentary_search_list = commentary_search_list_paginator.page(
                commentary_search_list_page)
        except PageNotAnInteger:
            commentary_search_list = commentary_search_list_paginator.page(1)
        except EmptyPage:
            commentary_search_list = commentary_search_list_paginator.page(
                commentary_search_list_paginator.num_pages)
        context['commentary_search_list'] = commentary_search_list

    if 'submission_search_queryset' in context:
        submission_search_list_paginator = Paginator(context['submission_search_queryset'], 10)
        submission_search_list_page = request.GET.get('submission_search_list_page')
        try:
            submission_search_list = submission_search_list_paginator.page(
                submission_search_list_page)
        except PageNotAnInteger:
            submission_search_list = submission_search_list_paginator.page(1)
        except EmptyPage:
            submission_search_list = submission_search_list_paginator.page(
                submission_search_list_paginator.num_pages)
        context['submission_search_list'] = submission_search_list

    return render(request, 'scipost/search.html', context)


#############
# Main view
#############

def index(request):
    """ Main page """
    context = {}
    context['latest_newsitems'] = NewsItem.objects.all().order_by('-date')[:2]
    context['issue'] = Issue.objects.get_last_filled_issue(in_volume__in_journal__name='SciPostPhys')
    if context['issue']:
        context['publications'] = context['issue'].publication_set.filter(doi_string__isnull=False
                                    ).order_by('-publication_date')[:4]

    return render(request, 'scipost/index.html', context)


###############
# Information
###############

def base(request):
    """ Skeleton for pages, used in template inheritance """
    return render(request, 'scipost/base.html')


def feeds(request):
    context = {'subject_areas_physics': SCIPOST_SUBJECT_AREAS[0][1]}
    return render(request, 'scipost/feeds.html', context)


################
# Contributors:
################

def register(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('personal_page')
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        Utils.load({'form': form})
        if form.is_valid():
            if Utils.password_mismatch():
                return render(request, 'scipost/register.html',
                              {'form': form, 'errormessage': 'Your passwords must match'})
            if Utils.username_already_taken():
                return render(request, 'scipost/register.html',
                              {'form': form, 'errormessage': 'This username is already in use'})
            if Utils.email_already_taken():
                return render(request, 'scipost/register.html',
                              {'form': form,
                               'errormessage': 'This email address is already in use'})
            Utils.create_and_save_contributor('')
            Utils.send_registration_email()
            # If this email was associated to an invitation, mark it as responded to
            try:
                invitation = RegistrationInvitation.objects.get(
                    email=form.cleaned_data['email'])
                invitation.responded = True
                invitation.save()
            except ObjectDoesNotExist:
                pass
            except MultipleObjectsReturned:
                # Delete the first invitation
                invitation_to_delete = RegistrationInvitation.objects.filter(
                    email=form.cleaned_data['email']).first()
                invitation_to_delete.delete()
            context = {'ack_header': 'Thanks for registering to SciPost.',
                       'ack_message': ('You will receive an email with a link to verify '
                                       'your email address. '
                                       'Please visit this link within 48 hours. '
                                       'Your credentials will thereafter be verified. '
                                       'If your registration is vetted through by the '
                                       'administrators, you will be enabled to contribute.'),
                       }
            return render(request, 'scipost/acknowledgement.html', context)
    else:
        form = RegistrationForm()
    invited = False
    context = {'form': form, 'invited': invited}
    return render(request, 'scipost/register.html', context)


def invitation(request, key):
    """ Register, by invitation """
    invitation = get_object_or_404(RegistrationInvitation, invitation_key=key)
    if invitation.responded:
        errormessage = ('This invitation token has already been used, '
                        'or this email address is already associated to a registration.')
    elif timezone.now() > invitation.key_expires:
        errormessage = 'The invitation key has expired.'
    elif request.method == 'POST':
        form = RegistrationForm(request.POST)
        Utils.load({'form': form})
        if form.is_valid():
            if Utils.password_mismatch():
                return render(request, 'scipost/register.html', {
                    'form': form, 'invited': True, 'key': key,
                    'errormessage': 'Your passwords must match'})
            if Utils.username_already_taken():
                return render(request, 'scipost/register.html',
                              {'form': form, 'invited': True, 'key': key,
                               'errormessage': 'This username is already in use'})
            if Utils.email_already_taken():
                return render(request, 'scipost/register.html',
                              {'form': form, 'invited': True, 'key': key,
                               'errormessage': 'This email address is already in use'})
            invitation.responded = True
            invitation.save()
            Utils.create_and_save_contributor(key)
            Utils.send_registration_email()
            context = {'ack_header': 'Thanks for registering to SciPost.',
                       'ack_message': ('You will receive an email with a link to verify '
                                       'your email address. '
                                       'Please visit this link within 48 hours. '
                                       'Your credentials will thereafter be verified. '
                                       'If your registration is vetted through by the '
                                       'administrators, you will be enabled to contribute.'),
                       }
            return render(request, 'scipost/acknowledgement.html', context)
        else:
            errormessage = 'form is invalidly filled'
            return render(request, 'scipost/register.html',
                          {'form': form, 'invited': True, 'key': key,
                           'errormessage': errormessage})
    else:
        form = RegistrationForm()
        form.fields['title'].initial = invitation.title
        form.fields['last_name'].initial = invitation.last_name
        form.fields['first_name'].initial = invitation.first_name
        form.fields['email'].initial = invitation.email
        errormessage = ''
        welcome_message = ('Welcome, ' + invitation.get_title_display() + ' '
                           + invitation.last_name + ', and thanks in advance for '
                           'registering (by completing this form)')
        return render(request, 'scipost/register.html', {
            'form': form, 'invited': True, 'key': key,
            'errormessage': errormessage, 'welcome_message': welcome_message})

    context = {'errormessage': errormessage}
    return render(request, 'scipost/accept_invitation_error.html', context)


def activation(request, key):
    """
    After registration, an email verification link is sent.
    Once clicked, the account is activated.
    """
    contributor = get_object_or_404(Contributor, activation_key=key)
    if not contributor.user.is_active:
        if timezone.now() > contributor.key_expires:
            context = {'oldkey': key}
            return render(request, 'scipost/request_new_activation_link.html', context)
        else:
            contributor.user.is_active = True
            contributor.user.save()
            context = {'ack_header': 'Your email address has been confirmed.',
                       'ack_message': ('Your SciPost account will soon be vetted. '
                                       'You will soon receive an email from us.'),
                       }
            return render(request, 'scipost/acknowledgement.html', context)
    else:
        return render(request, 'scipost/already_activated.html')


def request_new_activation_link(request, oldkey):
    contributor = get_object_or_404(Contributor, activation_key=oldkey)
    # Generate a new email activation key and link
    salt = ""
    for i in range(5):
        salt = salt + random.choice(string.ascii_letters)

    salt = salt.encode('utf8')
    usernamesalt = contributor.user.username
    usernamesalt = usernamesalt.encode('utf8')
    contributor.activation_key = hashlib.sha1(salt+usernamesalt).hexdigest()
    contributor.key_expires = datetime.datetime.strftime(
        datetime.datetime.now() + datetime.timedelta(days=2), "%Y-%m-%d %H:%M:%S")
    contributor.save()
    email_text = ('Dear ' + contributor.get_title_display() + ' ' + contributor.user.last_name +
                  ', \n\n'
                  'Your request for a new email activation link for registration to the SciPost '
                  'publication portal has been received. You now need to visit this link within '
                  'the next 48 hours: \n\n'
                  'https://scipost.org/activation/' + contributor.activation_key +
                  '\n\nYour registration will thereafter be vetted. Many thanks for your interest.'
                  '\n\nThe SciPost Team.')
    emailmessage = EmailMessage('SciPost registration: new email activation link',
                                email_text, 'SciPost registration <registration@scipost.org>',
                                [contributor.user.email, 'registration@scipost.org'],
                                reply_to=['registration@scipost.org'])
    emailmessage.send(fail_silently=False)
    context = {
        'ack_header': 'We have emailed you a new activation link.',
        'ack_message': ('Please acknowledge it within its 48 hours validity '
                        'window if you want us to proceed with vetting your registraion.'),
    }
    return render(request, 'scipost/acknowledgement.html', context)


def unsubscribe(request, key):
    """
    The link to this method is included in all email communications
    with a Contributor. The key used is the original activation key.
    At this link, the Contributor can confirm that he/she does not
    want to receive any non-essential email notifications from SciPost.
    """
    contributor = get_object_or_404(Contributor, activation_key=key)
    context = {'contributor': contributor, }
    return render(request, 'scipost/unsubscribe.html', context)


def unsubscribe_confirm(request, key):
    contributor = get_object_or_404(Contributor, activation_key=key)
    contributor.accepts_SciPost_emails = False
    contributor.save()
    context = {'ack_header': 'Unsubscribe',
               'followup_message': ('We have recorded your preference: you will '
                                    'no longer receive non-essential email '
                                    'from SciPost. You can go back to your '),
               'followup_link': reverse('scipost:personal_page'),
               'followup_link_label': 'personal page'}
    return render(request, 'scipost/acknowledgement.html', context)


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
    if request.method == 'POST':
        form = VetRegistrationForm(request.POST)
        contributor = Contributor.objects.get(pk=contributor_id)
        if form.is_valid():
            if form.cleaned_data['promote_to_registered_contributor']:
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

    context = {'ack_header': 'SciPost Registration request vetted.',
               'followup_message': 'Back to ',
               'followup_link': reverse('scipost:vet_registration_requests'),
               'followup_link_label': 'Registration requests page'}
    return render(request, 'scipost/acknowledgement.html', context)


@permission_required('scipost.can_draft_registration_invitations', return_403=True)
def draft_registration_invitation(request):
    """
    For officers to prefill registration invitations.
    This is similar to the registration_invitations method,
    which is used to complete the invitation process.
    """
    errormessage = ''
    if request.method == 'POST':
        draft_inv_form = DraftInvitationForm(request.POST)
        Utils.load({'contributor': request.user.contributor, 'form': draft_inv_form})
        if draft_inv_form.is_valid():
            if Utils.email_already_invited():
                errormessage = ('DUPLICATE ERROR: '
                                'This email address has already been used for an invitation')
            elif Utils.email_already_drafted():
                errormessage = ('DUPLICATE ERROR: '
                                'This email address has already been used for a draft invitation')
            elif Utils.email_already_taken():
                errormessage = ('DUPLICATE ERROR: '
                                'This email address is already associated to a Contributor')
            elif (draft_inv_form.cleaned_data['invitation_type'] == 'F'
                  and not request.user.has_perm('scipost.can_invite_Fellows')):
                errormessage = ('You do not have the authorization to send a Fellow-type '
                                'invitation. Consider Contributor, or cited (sub/pub). ')
            elif (draft_inv_form.cleaned_data['invitation_type'] == 'R'):
                errormessage = ('Referee-type invitations must be made by the Editor-in-charge '
                                'at the relevant Submission\'s Editorial Page. ')
            else:
                Utils.create_draft_invitation()
                context = {'ack_header': 'Draft invitation saved.',
                           'followup_message': 'Return to the ',
                           'followup_link': reverse('scipost:draft_registration_invitation'),
                           'followup_link_label': 'drafting page'}
                return render(request, 'scipost/acknowledgement.html', context)
        else:
            errormessage = 'The form was not filled validly.'

    else:
        draft_inv_form = DraftInvitationForm()

    sent_reg_inv = RegistrationInvitation.objects.filter(responded=False, declined=False)
    sent_reg_inv_fellows = sent_reg_inv.filter(invitation_type='F').order_by('last_name')
    nr_sent_reg_inv_fellows = sent_reg_inv_fellows.count()
    sent_reg_inv_contrib = sent_reg_inv.filter(invitation_type='C').order_by('last_name')
    nr_sent_reg_inv_contrib = sent_reg_inv_contrib.count()
    sent_reg_inv_ref = sent_reg_inv.filter(invitation_type='R').order_by('last_name')
    nr_sent_reg_inv_ref = sent_reg_inv_ref.count()
    sent_reg_inv_cited_sub = sent_reg_inv.filter(invitation_type='ci').order_by('last_name')
    nr_sent_reg_inv_cited_sub = sent_reg_inv_cited_sub.count()
    sent_reg_inv_cited_pub = sent_reg_inv.filter(invitation_type='cp').order_by('last_name')
    nr_sent_reg_inv_cited_pub = sent_reg_inv_cited_pub.count()

    resp_reg_inv = RegistrationInvitation.objects.filter(responded=True, declined=False)
    resp_reg_inv_fellows = resp_reg_inv.filter(invitation_type='F').order_by('last_name')
    nr_resp_reg_inv_fellows = resp_reg_inv_fellows.count()
    resp_reg_inv_contrib = resp_reg_inv.filter(invitation_type='C').order_by('last_name')
    nr_resp_reg_inv_contrib = resp_reg_inv_contrib.count()
    resp_reg_inv_ref = resp_reg_inv.filter(invitation_type='R').order_by('last_name')
    nr_resp_reg_inv_ref = resp_reg_inv_ref.count()
    resp_reg_inv_cited_sub = resp_reg_inv.filter(invitation_type='ci').order_by('last_name')
    nr_resp_reg_inv_cited_sub = resp_reg_inv_cited_sub.count()
    resp_reg_inv_cited_pub = resp_reg_inv.filter(invitation_type='cp').order_by('last_name')
    nr_resp_reg_inv_cited_pub = resp_reg_inv_cited_pub.count()

    decl_reg_inv = RegistrationInvitation.objects.filter(
        responded=True, declined=True).order_by('last_name')

    names_reg_contributors = Contributor.objects.filter(
        status=1).order_by('user__last_name').values_list(
        'user__first_name', 'user__last_name')
    existing_drafts = DraftInvitation.objects.filter(processed=False).order_by('last_name')

    context = {
        'draft_inv_form': draft_inv_form, 'errormessage': errormessage,
        'sent_reg_inv_fellows': sent_reg_inv_fellows,
        'nr_sent_reg_inv_fellows': nr_sent_reg_inv_fellows,
        'sent_reg_inv_contrib': sent_reg_inv_contrib,
        'nr_sent_reg_inv_contrib': nr_sent_reg_inv_contrib,
        'sent_reg_inv_ref': sent_reg_inv_ref,
        'nr_sent_reg_inv_ref': nr_sent_reg_inv_ref,
        'sent_reg_inv_cited_sub': sent_reg_inv_cited_sub,
        'nr_sent_reg_inv_cited_sub': nr_sent_reg_inv_cited_sub,
        'sent_reg_inv_cited_pub': sent_reg_inv_cited_pub,
        'nr_sent_reg_inv_cited_pub': nr_sent_reg_inv_cited_pub,
        'resp_reg_inv_fellows': resp_reg_inv_fellows,
        'nr_resp_reg_inv_fellows': nr_resp_reg_inv_fellows,
        'resp_reg_inv_contrib': resp_reg_inv_contrib,
        'nr_resp_reg_inv_contrib': nr_resp_reg_inv_contrib,
        'resp_reg_inv_ref': resp_reg_inv_ref,
        'nr_resp_reg_inv_ref': nr_resp_reg_inv_ref,
        'resp_reg_inv_cited_sub': resp_reg_inv_cited_sub,
        'nr_resp_reg_inv_cited_sub': nr_resp_reg_inv_cited_sub,
        'resp_reg_inv_cited_pub': resp_reg_inv_cited_pub,
        'nr_resp_reg_inv_cited_pub': nr_resp_reg_inv_cited_pub,
        'decl_reg_inv': decl_reg_inv,
        'names_reg_contributors': names_reg_contributors,
        'existing_drafts': existing_drafts,
    }
    return render(request, 'scipost/draft_registration_invitation.html', context)


@permission_required('scipost.can_manage_registration_invitations', return_403=True)
def edit_draft_reg_inv(request, draft_id):
    draft = get_object_or_404(DraftInvitation, id=draft_id)
    errormessage = ''
    if request.method == 'POST':
        draft_inv_form = DraftInvitationForm(request.POST)
        if draft_inv_form.is_valid():
            draft.title = draft_inv_form.cleaned_data['title']
            draft.first_name = draft_inv_form.cleaned_data['first_name']
            draft.last_name = draft_inv_form.cleaned_data['last_name']
            draft.email = draft_inv_form.cleaned_data['email']
            draft.save()
            return redirect(reverse('scipost:registration_invitations'))
        else:
            errormessage = 'The form is invalidly filled'
    else:
        draft_inv_form = DraftInvitationForm(instance=draft)
    context = {'draft_inv_form': draft_inv_form,
               'draft': draft,
               'errormessage': errormessage, }
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
    errormessage = ''
    associated_contributors = None
    if request.method == 'POST':
        # Send invitation from form information
        reg_inv_form = RegistrationInvitationForm(request.POST)
        Utils.load({'contributor': request.user.contributor, 'form': reg_inv_form})
        if reg_inv_form.is_valid():
            if Utils.email_already_invited():
                errormessage = ('DUPLICATE ERROR: '
                                'This email address has already been used for an invitation')
            elif Utils.email_already_taken():
                errormessage = ('DUPLICATE ERROR: '
                                'This email address is already associated to a Contributor')
            elif (reg_inv_form.cleaned_data['invitation_type'] == 'F'
                  and not request.user.has_perm('scipost.can_invite_Fellows')):
                errormessage = ('You do not have the authorization to send a Fellow-type '
                                'invitation. Consider Contributor, or cited (sub/pub). ')
            elif (reg_inv_form.cleaned_data['invitation_type'] == 'R'):
                errormessage = ('Referee-type invitations must be made by the Editor-in-charge '
                                'at the relevant Submission\'s Editorial Page. ')
            else:
                Utils.create_invitation()
                Utils.send_registration_invitation_email()
                try:
                    draft = DraftInvitation.objects.get(
                        email=reg_inv_form.cleaned_data['email'])
                    draft.processed = True
                    draft.save()
                except ObjectDoesNotExist:
                    pass
                except MultipleObjectsReturned:
                    # Delete the first invitation
                    draft_to_delete = RegistrationInvitation.objects.filter(
                        email=reg_inv_form.cleaned_data['email']).first()
                    draft_to_delete.delete()
                return HttpResponseRedirect('registration_invitation_sent')
        else:
            errormessage = 'The form was not filled validly.'

    else:
        initial = {}
        if draft_id:
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
        reg_inv_form = RegistrationInvitationForm(initial=initial)

    sent_reg_inv = RegistrationInvitation.objects.filter(responded=False, declined=False)
    sent_reg_inv_fellows = sent_reg_inv.filter(invitation_type='F').order_by('last_name')
    nr_sent_reg_inv_fellows = sent_reg_inv_fellows.count()
    sent_reg_inv_contrib = sent_reg_inv.filter(invitation_type='C').order_by('last_name')
    nr_sent_reg_inv_contrib = sent_reg_inv_contrib.count()
    sent_reg_inv_ref = sent_reg_inv.filter(invitation_type='R').order_by('last_name')
    nr_sent_reg_inv_ref = sent_reg_inv_ref.count()
    sent_reg_inv_cited_sub = sent_reg_inv.filter(invitation_type='ci').order_by('last_name')
    nr_sent_reg_inv_cited_sub = sent_reg_inv_cited_sub.count()
    sent_reg_inv_cited_pub = sent_reg_inv.filter(invitation_type='cp').order_by('last_name')
    nr_sent_reg_inv_cited_pub = sent_reg_inv_cited_pub.count()

    resp_reg_inv = RegistrationInvitation.objects.filter(responded=True, declined=False)
    resp_reg_inv_fellows = resp_reg_inv.filter(invitation_type='F').order_by('last_name')
    nr_resp_reg_inv_fellows = resp_reg_inv_fellows.count()
    resp_reg_inv_contrib = resp_reg_inv.filter(invitation_type='C').order_by('last_name')
    nr_resp_reg_inv_contrib = resp_reg_inv_contrib.count()
    resp_reg_inv_ref = resp_reg_inv.filter(invitation_type='R').order_by('last_name')
    nr_resp_reg_inv_ref = resp_reg_inv_ref.count()
    resp_reg_inv_cited_sub = resp_reg_inv.filter(invitation_type='ci').order_by('last_name')
    nr_resp_reg_inv_cited_sub = resp_reg_inv_cited_sub.count()
    resp_reg_inv_cited_pub = resp_reg_inv.filter(invitation_type='cp').order_by('last_name')
    nr_resp_reg_inv_cited_pub = resp_reg_inv_cited_pub.count()

    decl_reg_inv = RegistrationInvitation.objects.filter(responded=True, declined=True)

    names_reg_contributors = Contributor.objects.filter(
        status=1).order_by('user__last_name').values_list(
        'user__first_name', 'user__last_name')
    existing_drafts = DraftInvitation.objects.filter(processed=False).order_by('last_name')

    context = {
        'reg_inv_form': reg_inv_form, 'errormessage': errormessage,
        'sent_reg_inv_fellows': sent_reg_inv_fellows,
        'nr_sent_reg_inv_fellows': nr_sent_reg_inv_fellows,
        'sent_reg_inv_contrib': sent_reg_inv_contrib,
        'nr_sent_reg_inv_contrib': nr_sent_reg_inv_contrib,
        'sent_reg_inv_ref': sent_reg_inv_ref,
        'nr_sent_reg_inv_ref': nr_sent_reg_inv_ref,
        'sent_reg_inv_cited_sub': sent_reg_inv_cited_sub,
        'nr_sent_reg_inv_cited_sub': nr_sent_reg_inv_cited_sub,
        'sent_reg_inv_cited_pub': sent_reg_inv_cited_pub,
        'nr_sent_reg_inv_cited_pub': nr_sent_reg_inv_cited_pub,
        'resp_reg_inv_fellows': resp_reg_inv_fellows,
        'nr_resp_reg_inv_fellows': nr_resp_reg_inv_fellows,
        'resp_reg_inv_contrib': resp_reg_inv_contrib,
        'nr_resp_reg_inv_contrib': nr_resp_reg_inv_contrib,
        'resp_reg_inv_ref': resp_reg_inv_ref,
        'nr_resp_reg_inv_ref': nr_resp_reg_inv_ref,
        'resp_reg_inv_cited_sub': resp_reg_inv_cited_sub,
        'nr_resp_reg_inv_cited_sub': nr_resp_reg_inv_cited_sub,
        'resp_reg_inv_cited_pub': resp_reg_inv_cited_pub,
        'nr_resp_reg_inv_cited_pub': nr_resp_reg_inv_cited_pub,
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
    redirect_to = request.POST.get('next',
                                   request.GET.get('next', reverse('scipost:personal_page')))
    redirect_to = (redirect_to
                   if is_safe_url(redirect_to, request.get_host())
                   else reverse('scipost:personal_page'))
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None and is_registered(user):
            if user.is_active:
                login(request, user)
                return redirect(redirect_to)
            else:
                return render(request, 'scipost/disabled_account.html')
        else:
            return render(request, 'scipost/login_error.html')
    else:
        form = AuthenticationForm()
        return render(request, 'scipost/login.html', {'form': form, 'next': redirect_to})


def logout_view(request):
    logout(request)
    return render(request, 'scipost/logout.html')


def mark_unavailable_period(request):
    if request.method == 'POST':
        unav_form = UnavailabilityPeriodForm(request.POST)
        errormessage = None
        if unav_form.is_valid():
            now = timezone.now()
            if unav_form.cleaned_data['start'] > unav_form.cleaned_data['end']:
                errormessage = 'The start date you have entered is later than the end date.'
            elif unav_form.cleaned_data['end'] < now.date():
                errormessage = 'You have entered an end date in the past.'
            if errormessage is not None:
                return render(request, 'scipost/error.html',
                              context={'errormessage': errormessage})
            else:
                unav = UnavailabilityPeriod(
                    contributor=request.user.contributor,
                    start=unav_form.cleaned_data['start'],
                    end=unav_form.cleaned_data['end'])
                unav.save()
        else:
            errormessage = 'Please enter valid dates (format: YYYY-MM-DD).'
            return render(request, 'scipost/error.html', context={'errormessage': errormessage})
    return redirect('scipost:personal_page')


@login_required
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
    if is_SP_Admin(contributor.user):
        intwodays = now + timezone.timedelta(days=2)

        # count the number of pending registration requests
        nr_reg_to_vet = Contributor.objects.filter(user__is_active=True, status=0).count()
        nr_reg_awaiting_validation = Contributor.objects.filter(
            user__is_active=False, key_expires__gte=now,
            key_expires__lte=intwodays, status=0).count()
        nr_submissions_to_assign = Submission.objects.filter(status__in=['unassigned']).count()
        nr_recommendations_to_prepare_for_voting = EICRecommendation.objects.filter(
            submission__status__in=['voting_in_preparation']).count()
    nr_assignments_to_consider = 0
    active_assignments = None
    nr_reports_to_vet = 0
    if is_MEC(contributor.user):
        nr_assignments_to_consider = (EditorialAssignment.objects
                                      .filter(to=contributor, accepted=None, deprecated=False)
                                      .count())
        active_assignments = EditorialAssignment.objects.filter(
            to=contributor, accepted=True, completed=False)
        nr_reports_to_vet = Report.objects.filter(
            status=0, submission__editor_in_charge=contributor).count()
    nr_commentary_page_requests_to_vet = 0
    nr_comments_to_vet = 0
    nr_thesislink_requests_to_vet = 0
    nr_authorship_claims_to_vet = 0
    if is_VE(request.user):
        nr_commentary_page_requests_to_vet = Commentary.objects.filter(vetted=False).count()
        nr_comments_to_vet = Comment.objects.filter(status=0).count()
        nr_thesislink_requests_to_vet = ThesisLink.objects.filter(vetted=False).count()
        nr_authorship_claims_to_vet = AuthorshipClaim.objects.filter(status='0').count()
    nr_ref_inv_to_consider = RefereeInvitation.objects.filter(
        referee=contributor, accepted=None, cancelled=False).count()
    pending_ref_tasks = RefereeInvitation.objects.filter(
        referee=contributor, accepted=True, fulfilled=False)
    # Verify if there exist objects authored by this contributor,
    # whose authorship hasn't been claimed yet
    own_submissions = (Submission.objects
                       .filter(authors__in=[contributor], is_current=True)
                       .order_by('-submission_date'))
    own_commentaries = (Commentary.objects
                        .filter(authors__in=[contributor])
                        .order_by('-latest_activity'))
    own_thesislinks = ThesisLink.objects.filter(author_as_cont__in=[contributor])
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
    own_comments = (Comment.objects.select_related('author', 'submission')
                    .filter(author=contributor, is_author_reply=False)
                    .order_by('-date_submitted'))
    own_authorreplies = (Comment.objects
                         .filter(author=contributor, is_author_reply=True)
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
        'nr_submission_authorships_to_claim': nr_submission_authorships_to_claim,
        'nr_commentary_authorships_to_claim': nr_commentary_authorships_to_claim,
        'nr_thesis_authorships_to_claim': nr_thesis_authorships_to_claim,
        'nr_ref_inv_to_consider': nr_ref_inv_to_consider,
        'pending_ref_tasks': pending_ref_tasks,
        'own_submissions': own_submissions,
        'own_commentaries': own_commentaries,
        'own_thesislinks': own_thesislinks,
        'own_comments': own_comments, 'own_authorreplies': own_authorreplies,
    }
    return render(request, 'scipost/personal_page.html', context)


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        ack = False
        if form.is_valid():
            if not request.user.check_password(form.cleaned_data['password_prev']):
                return render(
                    request, 'scipost/change_password.html',
                    {'form': form,
                     'errormessage': 'The currently existing password you entered is incorrect'})
            if form.cleaned_data['password_new'] != form.cleaned_data['password_verif']:
                return render(request, 'scipost/change_password.html', {
                              'form': form,
                              'errormessage': 'Your new password entries must match'})
            request.user.set_password(form.cleaned_data['password_new'])
            request.user.save()
            ack = True
        context = {'ack': ack, 'form': form}
    else:
        form = PasswordChangeForm()
        context = {'ack': False, 'form': form}
    return render(request, 'scipost/change_password.html', context)


def reset_password_confirm(request, uidb64=None, token=None):
    return password_reset_confirm(request, template_name='scipost/reset_password_confirm.html',
                                  uidb64=uidb64, token=token,
                                  post_reset_redirect=reverse('scipost:login'))


def reset_password(request):
    return password_reset(request, template_name='scipost/reset_password.html',
                          email_template_name='scipost/reset_password_email.html',
                          subject_template_name='scipost/reset_password_subject.txt',
                          post_reset_redirect=reverse('scipost:login'))


@login_required
def update_personal_data(request):
    contributor = Contributor.objects.get(user=request.user)
    if request.method == 'POST':
        user_form = UpdateUserDataForm(request.POST)
        cont_form = UpdatePersonalDataForm(request.POST)
        if user_form.is_valid() and cont_form.is_valid():
            request.user.email = user_form.cleaned_data['email']
            request.user.first_name = user_form.cleaned_data['first_name']
            request.user.contributor.title = cont_form.cleaned_data['title']
            request.user.contributor.discipline = cont_form.cleaned_data['discipline']
            request.user.contributor.expertises = cont_form.cleaned_data['expertises']
            request.user.contributor.orcid_id = cont_form.cleaned_data['orcid_id']
            request.user.contributor.country_of_employment = cont_form.cleaned_data['country_of_employment']
            request.user.contributor.address = cont_form.cleaned_data['address']
            request.user.contributor.affiliation = cont_form.cleaned_data['affiliation']
            request.user.contributor.personalwebpage = cont_form.cleaned_data['personalwebpage']
            request.user.contributor.accepts_SciPost_emails = cont_form.cleaned_data['accepts_SciPost_emails']
            request.user.save()
            request.user.contributor.save()
            context = {'ack_header': 'Your personal data has been updated.',
                       'followup_message': 'Return to your ',
                       'followup_link': reverse('scipost:personal_page'),
                       'followup_link_label': 'personal page'}
            return render(request, 'scipost/acknowledgement.html', context)
    else:
        user_form = UpdateUserDataForm(instance=contributor.user)
        # Prevent exploit of gaining view on self-authored submissions by changing surname.
        user_form.fields['last_name'].widget.attrs['disabled'] = True
        # Surname can only be changed through the admin.
        cont_form = UpdatePersonalDataForm(instance=contributor)
    return render(request, 'scipost/update_personal_data.html',
                  {'user_form': user_form, 'cont_form': cont_form})


@login_required
def claim_authorships(request):
    """
    The system auto-detects potential authorships (of submissions,
    papers subject to commentaries, theses, ...).
    The contributor must confirm/deny authorship from the
    Personal Page.
    """
    contributor = Contributor.objects.get(user=request.user)

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

    context = {'submission_authorships_to_claim': submission_authorships_to_claim,
               'sub_auth_claim_form': sub_auth_claim_form,
               'commentary_authorships_to_claim': commentary_authorships_to_claim,
               'com_auth_claim_form': com_auth_claim_form,
               'thesis_authorships_to_claim': thesis_authorships_to_claim,
               'thesis_auth_claim_form': thesis_auth_claim_form,
               }
    return render(request, 'scipost/claim_authorships.html', context)


@login_required
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
    contributor = Contributor.objects.get(pk=contributor_id)
    contributor_publications = Publication.objects.published().filter(authors=contributor)
    contributor_submissions = Submission.objects.public().filter(authors=contributor)
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
    if request.method == 'POST':
        form = EmailGroupMembersForm(request.POST)
        if form.is_valid():
            # recipient_emails = []
            # for member in form.cleaned_data['group'].user_set.all():
            #     recipient_emails.append(member.email)
            # emailmessage = EmailMessage(
            #     form.cleaned_data['email_subject'],
            #     form.cleaned_data['email_text'],
            #     'SciPost Admin <admin@scipost.org>',
            #     ['admin@scipost.org'],
            #     bcc=recipient_emails,
            #     reply_to=['admin@scipost.org'])
            # emailmessage.send(fail_silently=False)
            # with mail.get_connection() as connection:
            #     for member in form.cleaned_data['group'].user_set.all():
            #         email_text = ('Dear ' + member.contributor.get_title_display() + ' ' +
            #                       member.last_name + ', \n\n'
            #                       + form.cleaned_data['email_text'])
            #         mail.EmailMessage(form.cleaned_data['email_subject'],
            #                           email_text, 'SciPost Admin <admin@scipost.org>',
            #                           [member.email], connection=connection).send()
            group_members = form.cleaned_data['group'].user_set.all()
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
                            email_text += ('\n\nDon\'t want to receive such emails? '
                                           'Unsubscribe by visiting '
                                           'https://scipost.org/unsubscribe/'
                                           + member.contributor.activation_key + '.')
                            email_text_html += (
                                '<br/>\n<p style="font-size: 10px;">Don\'t want to receive such '
                                'emails? <a href="https://scipost.org/unsubscribe/{{ key }}">'
                                'Unsubscribe</a>.</p>')
                            email_context = Context({
                                'title': member.contributor.get_title_display(),
                                'last_name': member.last_name,
                                'email_text': form.cleaned_data['email_text'],
                                'key': member.contributor.activation_key,
                            })
                            html_template = Template(email_text_html)
                            html_version = html_template.render(email_context)
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
        else:
            errormessage = 'The form was invalidly filled.'
            context = {'errormessage': errormessage, 'form': form}
            return render(request, 'scipost/email_group_members.html', context)
    form = EmailGroupMembersForm()
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
            email_context = Context({'email_text': form.cleaned_data['email_text']})
            if form.cleaned_data['include_scipost_summary']:
                email_text += SCIPOST_SUMMARY_FOOTER
                email_text_html += SCIPOST_SUMMARY_FOOTER_HTML

            email_text_html += '<br/>' + EMAIL_FOOTER
            html_template = Template(email_text_html)
            html_version = html_template.render(email_context)
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
    if request.method == 'POST':
        form = SendPrecookedEmailForm(request.POST)
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
            email_context = Context({'email_text': precookedEmail.email_text_html})
            if form.cleaned_data['include_scipost_summary']:
                email_text += SCIPOST_SUMMARY_FOOTER
                email_text_html += SCIPOST_SUMMARY_FOOTER_HTML

            email_text_html += '<br/>' + EMAIL_FOOTER
            html_template = Template(email_text_html)
            html_version = html_template.render(email_context)
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
    form = SendPrecookedEmailForm()
    context = {'form': form}
    return render(request, 'scipost/send_precooked_email.html', context)


#####################
# Editorial College #
#####################

def EdCol_bylaws(request):
    return render(request, 'scipost/EdCol_by-laws.html')


@permission_required('scipost.can_view_pool', return_403=True)
def Fellow_activity_overview(request, Fellow_id=None):
    fellows = Contributor.objects.filter(
        user__groups__name='Editorial College').order_by('user__last_name')
    context = {'fellows': fellows}
    if Fellow_id:
        fellow = get_object_or_404(Contributor, pk=Fellow_id)
        context['fellow'] = fellow

        assignments_ongoing = (EditorialAssignment.objects.get_for_user_in_pool(request.user)
                               .filter(accepted=True, completed=False, to=fellow)
                               .order_by('-date_created'))
        context['assignments_ongoing'] = assignments_ongoing

        assignments_completed = (EditorialAssignment.objects.get_for_user_in_pool(request.user)
                                 .filter(completed=True, to=fellow).order_by('-date_created'))
        context['assignments_completed'] = assignments_completed
    return render(request, 'scipost/Fellow_activity_overview.html', context)


#############################
# Supporting Partners Board #
#############################

def supporting_partners(request):
    prospective_agreements = SPBMembershipAgreement.objects.filter(
        status='Submitted').order_by('date_requested')
    context = {'prospective_partners': prospective_agreements, }
    return render(request, 'scipost/supporting_partners.html', context)


@login_required
def SPB_membership_request(request):
    errormessage = ''
    if request.method == 'POST':
        SP_form = SupportingPartnerForm(request.POST)
        membership_form = SPBMembershipForm(request.POST)
        if SP_form.is_valid() and membership_form.is_valid():
            partner = SupportingPartner(
                partner_type=SP_form.cleaned_data['partner_type'],
                status='Prospective',
                institution=SP_form.cleaned_data['institution'],
                institution_acronym=SP_form.cleaned_data['institution_acronym'],
                institution_address=SP_form.cleaned_data['institution_address'],
                contact_person=request.user.contributor,
            )
            partner.save()
            agreement = SPBMembershipAgreement(
                partner=partner,
                status='Submitted',
                date_requested=timezone.now().date(),
                start_date=membership_form.cleaned_data['start_date'],
                duration=membership_form.cleaned_data['duration'],
                offered_yearly_contribution=membership_form.cleaned_data['offered_yearly_contribution'],
            )
            agreement.save()
            ack_message = ('Thank you for your SPB Membership request. '
                           'We will get back to you in the very near future '
                           'with details of the proposed agreement.')
            context = {'ack_message': ack_message, }
            return render(request, 'scipost/acknowledgement.html', context)
        else:
            errormessage = 'The form was not filled properly.'

    else:
        SP_form = SupportingPartnerForm()
        membership_form = SPBMembershipForm()
    context = {'errormessage': errormessage,
               'SP_form': SP_form,
               'membership_form': membership_form, }
    return render(request, 'scipost/SPB_membership_request.html', context)


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
