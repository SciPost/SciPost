import datetime
import hashlib
import random
import re
import string

from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required 
#from django.contrib.auth.decorators import permission_required   # Superseded by guardian
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.views import password_reset, password_reset_confirm
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect
from django.template import RequestContext
from django.utils.http import is_safe_url
from django.views.decorators.csrf import csrf_protect
from django.db.models import Avg

from guardian.decorators import permission_required
from guardian.decorators import permission_required_or_403
from guardian.shortcuts import assign_perm

from .models import *
from .forms import *

from .global_methods import *
from .utils import *


from commentaries.models import Commentary
from commentaries.forms import CommentarySearchForm
from comments.models import Comment
from submissions.models import Submission, EditorialAssignment, RefereeInvitation, Report
from submissions.forms import SubmissionSearchForm
from theses.models import ThesisLink
from theses.forms import ThesisLinkSearchForm


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
    commentary_query = get_query(query, 
                                 ['pub_title', 'author_list', 'pub_abstract'])
    submission_query = get_query(query, 
                                 ['title', 'author_list', 'abstract'])
    thesislink_query = get_query(query, 
                                 ['title', 'author', 'abstract', 'supervisor'])
    comment_query = get_query(query,
                              ['comment_text'])

    commentary_search_list = Commentary.objects.filter(
        commentary_query,
        vetted=True,
        ).order_by('-pub_date')
    submission_search_list = Submission.objects.filter(
        submission_query,
        status__gte=1,
        ).order_by('-submission_date')
    thesislink_search_list = ThesisLink.objects.filter(
        thesislink_query,
        vetted=True,
        ).order_by('-defense_date')
    comment_search_list = Comment.objects.filter(
        comment_query,
        status__gte='1',
        ).order_by('-date_submitted')
    context = {'commentary_search_list': commentary_search_list,
               'submission_search_list': submission_search_list,
               'thesislink_search_list': thesislink_search_list,
               'comment_search_list': comment_search_list}
    return context


def search(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            context = documentsSearchResults(form.cleaned_data['query'])
        else:
            context = {}
    else:
        context = {}
    return render(request, 'scipost/search.html', context)


#############
# Main view
#############

def index(request):
    submission_search_form = SubmissionSearchForm(request.POST)
    commentary_search_form = CommentarySearchForm(request.POST)
    thesislink_search_form = ThesisLinkSearchForm(request.POST)
    context = {'submission_search_form': submission_search_form, 
               'commentary_search_form': commentary_search_form, 
               'thesislink_search_form': thesislink_search_form,
               }
    return render(request, 'scipost/index.html', context)

###############
# Information
###############

def base(request):
    return render(request, 'scipost/base.html')


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
                              {'form': form, 'errormessage': 'This email address is already in use'})
            Utils.create_and_save_contributor('')
            Utils.send_registration_email()
            return HttpResponseRedirect(reverse('scipost:thanks_for_registering'))
    else:
        form = RegistrationForm()
    invited = False
    context = {'form': form, 'invited': invited}
    return render(request, 'scipost/register.html', context)


def invitation(request, key):
    """ Register, by invitation """
    invitation = get_object_or_404(RegistrationInvitation, invitation_key=key)
    if invitation.responded:
        errormessage = 'This invitation token has already been used.'
    elif timezone.now() > invitation.key_expires:
        errormessage = 'The invitation key has expired.'
    elif request.method == 'POST':
        form = RegistrationForm(request.POST)
        Utils.load({'form': form})
        if form.is_valid():
            if Utils.password_mismatch():
                return render(request, 'scipost/register.html',
                                {'form': form, 'invited': True, 'key': key, 'errormessage': 'Your passwords must match'})
            if Utils.username_already_taken():
                return render(request, 'scipost/register.html',
                              {'form': form, 'invited': True, 'key': key, 'errormessage': 'This username is already in use'})
            if Utils.email_already_taken():
                return render(request, 'scipost/register.html',
                              {'form': form, 'invited': True, 'key': key, 'errormessage': 'This email address is already in use'})
            invitation.responded = True
            invitation.save()
            Utils.create_and_save_contributor(key)
            Utils.send_registration_email()
            return HttpResponseRedirect(reverse('scipost:thanks_for_registering'))
        else:
            errormessage = 'form is invalidly filled'
            return render(request, 'scipost/register.html',
                          {'form': form, 'invited': True, 'key': key, 'errormessage': errormessage})
    else:
        form = RegistrationForm()
        form.fields['title'].initial = invitation.title
        form.fields['last_name'].initial = invitation.last_name
        form.fields['first_name'].initial = invitation.first_name
        form.fields['email'].initial = invitation.email
        errormessage = ''
        welcome_message = 'Welcome, ' + title_dict[invitation.title] + ' ' + invitation.last_name + ', and thanks in advance for registering (by completing this form)'
        return render(request, 'scipost/register.html',
                        {'form': form, 'invited': True, 'key': key, 'errormessage': errormessage, 'welcome_message': welcome_message})

    context = {'errormessage': errormessage}
    return render(request, 'scipost/accept_invitation_error.html', context)



def activation(request, key):
#    activation_expired = False
#    already_active = False
    contributor = get_object_or_404(Contributor, activation_key=key)
    if contributor.user.is_active == False:
        if timezone.now() > contributor.key_expires:
#            activation_expired = True
            id_user = contributor.user.id
            context = {'oldkey': key}
            return render(request, 'scipost/request_new_activation_link.html', context)
        else: 
            contributor.user.is_active = True
            contributor.user.save()
            return render(request, 'scipost/activation_ack.html')
    else:
#        already_active = True
        return render(request, 'scipost/already_activated.html')
#    # will never come beyond here
#    return render(request, 'scipost/index.html')



def request_new_activation_link(request, oldkey):
    contributor = get_object_or_404(Contributor, activation_key=oldkey)
    # Generate a new email activation key and link
    salt = ""
    for i in range(5):
        salt = salt + random.choice(string.ascii_letters)
            #salt = hashlib.sha1(str(random.random()).encode('utf8')).hexdigest()[:5]
    salt = salt.encode('utf8')
    usernamesalt = contributor.user.username
    usernamesalt = usernamesalt.encode('utf8')
    contributor.activation_key = hashlib.sha1(salt+usernamesalt).hexdigest()
    contributor.key_expires = datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(days=2), "%Y-%m-%d %H:%M:%S")
    contributor.save()
    email_text = ('Dear ' + title_dict[contributor.title] + ' ' + contributor.user.last_name + 
                  ', \n\nYour request for a new email activation link for registration to the SciPost ' +
                  'publication portal has been received. You now need to visit this link within the next 48 hours: \n\n' + 
                  'https://scipost.org/activation/' + contributor.activation_key + 
                  '\n\nYour registration will thereafter be vetted. Many thanks for your interest.  \n\nThe SciPost Team.')
    emailmessage = EmailMessage('SciPost registration: new email activation link', email_text, 'SciPost registration <registration@scipost.org>', 
                                [contributor.user.email, 'registration@scipost.org'], reply_to=['registration@scipost.org'])
    emailmessage.send(fail_silently=False)
    return render (request, 'scipost/request_new_activation_link_ack.html')


@permission_required('scipost.can_vet_registration_requests', return_403=True)
def vet_registration_requests(request):
    contributor = Contributor.objects.get(user=request.user)
    contributors_to_vet = Contributor.objects.filter(user__is_active=True, status=0).order_by('key_expires')
    reg_cont_group = Group.objects.get(name='Registered Contributors')
    form = VetRegistrationForm()
    context = {'contributors_to_vet': contributors_to_vet, 'form': form }
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
                    pending_ref_inv = RefereeInvitation.objects.get(invitation_key=contributor.invitation_key)
                    pending_ref_inv.referee = contributor
                    pending_ref_inv.save()
                except RefereeInvitation.DoesNotExist:
                    pending_ref_inv_exists = False

                email_text = ('Dear ' + title_dict[contributor.title] + ' ' + contributor.user.last_name + 
                              ', \n\nYour registration to the SciPost publication portal has been accepted. ' +
                              'You can now login at https://scipost.org and contribute. \n\n')
                if pending_ref_inv_exists:
                    email_text += ('Note that you have pending refereeing invitations; please navigate to '
                                   'https://scipost.org/submissions/accept_or_decline_ref_invitations '
                                   '(login required) to accept or decline them.\n\n')
                email_text += 'Thank you very much in advance, \nThe SciPost Team.'
                emailmessage = EmailMessage('SciPost registration accepted', email_text,
                                            'SciPost registration <registration@scipost.org>', 
                                            [contributor.user.email, 'registration@scipost.org'], 
                                            reply_to=['registration@scipost.org'])
                emailmessage.send(fail_silently=False)
            else:
                ref_reason = int(form.cleaned_data['refusal_reason'])
                email_text = ('Dear ' + title_dict[contributor.title] + ' ' + contributor.user.last_name + 
                              ', \n\nYour registration to the SciPost publication portal has been turned down, the reason being: ' + 
                              reg_ref_dict[ref_reason] + '. You can however still view all SciPost contents, just not submit papers, ' +
                              'comments or votes. We nonetheless thank you for your interest. \n\nThe SciPost Team.')
                if form.cleaned_data['email_response_field']:
                    email_text += '\n\nFurther explanations: ' + form.cleaned_data['email_response_field']
                emailmessage = EmailMessage('SciPost registration: unsuccessful', email_text, 'SciPost registration <registration@scipost.org>', 
                                            [contributor.user.email, 'registration@scipost.org'], reply_to=['registration@scipost.org'])
                emailmessage.send(fail_silently=False)
                contributor.status = form.cleaned_data['refusal_reason']
                contributor.save()

    context = {}
    return render(request, 'scipost/vet_registration_request_ack.html', context)


@permission_required('scipost.can_manage_registration_invitations', return_403=True)
def registration_invitations(request):
    # List invitations sent; send new ones
    errormessage = ''
    if request.method == 'POST':
        # Send invitation from form information
        reg_inv_form = RegistrationInvitationForm(request.POST)
        Utils.load({'contributor': request.user.contributor, 'form': reg_inv_form})
        if reg_inv_form.is_valid():
            if Utils.email_already_invited():
                errormessage = 'DUPLICATE ERROR: This email address has already been used for an invitation'
            elif Utils.email_already_taken():
                errormessage = 'DUPLICATE ERROR: This email address is already associated to a Contributor'
            else:
                Utils.create_invitation()
                Utils.send_registration_invitation_email()
                return HttpResponseRedirect('registration_invitation_sent')
    else:
        reg_inv_form = RegistrationInvitationForm()
    sent_reg_inv_fellows = RegistrationInvitation.objects.filter(invitation_type='F', responded=False).order_by('last_name')
    nr_sent_reg_inv_fellows = sent_reg_inv_fellows.count()
    sent_reg_inv_contrib = RegistrationInvitation.objects.filter(invitation_type='C', responded=False).order_by('last_name')
    nr_sent_reg_inv_contrib = sent_reg_inv_contrib.count()
    resp_reg_inv_fellows = RegistrationInvitation.objects.filter(invitation_type='F', responded=True).order_by('last_name')
    nr_resp_reg_inv_fellows = resp_reg_inv_fellows.count()
    resp_reg_inv_contrib = RegistrationInvitation.objects.filter(invitation_type='C', responded=True).order_by('last_name')
    nr_resp_reg_inv_contrib = resp_reg_inv_contrib.count()
    context = {'reg_inv_form': reg_inv_form, 'errormessage': errormessage,
               'sent_reg_inv_fellows': sent_reg_inv_fellows, 'nr_sent_reg_inv_fellows': nr_sent_reg_inv_fellows,
               'sent_reg_inv_contrib': sent_reg_inv_contrib, 'nr_sent_reg_inv_contrib': nr_sent_reg_inv_contrib,
               'resp_reg_inv_fellows': resp_reg_inv_fellows, 'nr_resp_reg_inv_fellows': nr_resp_reg_inv_fellows,
               'resp_reg_inv_contrib': resp_reg_inv_contrib, 'nr_resp_reg_inv_contrib': nr_resp_reg_inv_contrib }
    return render(request, 'scipost/registration_invitations.html', context)



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
                contributor = Contributor.objects.get(user=request.user)
                context = {'contributor': contributor }
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


def personal_page(request):
    if request.user.is_authenticated():
        contributor = Contributor.objects.get(user=request.user)
        # if an editor, count the number of actions required:
        nr_reg_to_vet = 0
        nr_reg_awaiting_validation = 0
        nr_submissions_to_assign = 0
        if is_SP_Admin(request.user):
            now = timezone.now()
            intwodays = now + timezone.timedelta(days=2)
            # count the number of pending registration requests
            nr_reg_to_vet = Contributor.objects.filter(user__is_active=True, status=0).count()
            nr_reg_awaiting_validation = Contributor.objects.filter(
                user__is_active=False, key_expires__gte=now, key_expires__lte=intwodays, status=0).count()
            nr_submissions_to_assign = Submission.objects.filter(status__in=['unassigned']).count()
        nr_assignments_to_consider = 0
        active_assignments = None
        nr_reports_to_vet = 0
        if is_MEC(request.user):
            nr_assignments_to_consider = (EditorialAssignment.objects
                                          .filter(to=contributor, accepted=None, deprecated=False)
                                          .count())
            active_assignments = EditorialAssignment.objects.filter(to=contributor, accepted=True, completed=False)
            nr_reports_to_vet = Report.objects.filter(status=0, submission__editor_in_charge=contributor).count()
        nr_commentary_page_requests_to_vet = 0
        nr_comments_to_vet = 0
        nr_thesislink_requests_to_vet = 0
        nr_authorship_claims_to_vet = 0
        if is_VE(request.user):
            nr_commentary_page_requests_to_vet = Commentary.objects.filter(vetted=False).count()
            nr_comments_to_vet = Comment.objects.filter(status=0).count()
            nr_thesislink_requests_to_vet = ThesisLink.objects.filter(vetted=False).count()
            nr_authorship_claims_to_vet = AuthorshipClaim.objects.filter(status='0').count()
        nr_ref_inv_to_consider = RefereeInvitation.objects.filter(referee=contributor, accepted=None).count()
        pending_ref_tasks = RefereeInvitation.objects.filter(referee=contributor, accepted=True, fulfilled=False)
        # Verify if there exist objects authored by this contributor, whose authorship hasn't been claimed yet
        own_submissions = (Submission.objects
                           #.filter(Q(authors__in=[contributor]) | Q(submitted_by=contributor)) # submitters must be authors
                           .filter(authors__in=[contributor])
                           .order_by('-submission_date'))
        own_commentaries = (Commentary.objects
                            .filter(authors__in=[contributor])
                            .order_by('-latest_activity'))
        own_thesislinks = ThesisLink.objects.filter(author_as_cont__in=[contributor])
        nr_submission_authorships_to_claim = (Submission.objects
                                              .filter(author_list__contains=contributor.user.last_name)
                                              .exclude(authors__in=[contributor])
                                              .exclude(authors_claims__in=[contributor])
                                              .exclude(authors_false_claims__in=[contributor])
                                              .count())
        nr_commentary_authorships_to_claim = (Commentary.objects
                                              .filter(author_list__contains=contributor.user.last_name)
                                              .exclude(authors__in=[contributor])
                                              .exclude(authors_claims__in=[contributor])
                                              .exclude(authors_false_claims__in=[contributor])
                                              .count())
        nr_thesis_authorships_to_claim = (ThesisLink.objects
                                          .filter(author__contains=contributor.user.last_name)
                                          .exclude(author_as_cont__in=[contributor])
                                          .exclude(author_claims__in=[contributor])
                                          .exclude(author_false_claims__in=[contributor])
                                          .count())
        own_comments = (Comment.objects
                        .filter(author=contributor,is_author_reply=False)
                        .order_by('-date_submitted'))
        own_authorreplies = (Comment.objects
                             .filter(author=contributor,is_author_reply=True)
                             .order_by('-date_submitted'))
        lists_owned = List.objects.filter(owner=contributor)
        lists = List.objects.filter(teams_with_access__members__in=[contributor])
        teams_led = Team.objects.filter(leader=contributor)
        teams = Team.objects.filter(members__in=[contributor])
        graphs_owned = Graph.objects.filter(owner=contributor)
        graphs_private = Graph.objects.filter(Q(teams_with_access__leader=contributor) 
                                              | Q(teams_with_access__members__in=[contributor]))
        context = {'contributor': contributor, 
                   'nr_reg_to_vet': nr_reg_to_vet, 
                   'nr_reg_awaiting_validation': nr_reg_awaiting_validation, 
                   'nr_commentary_page_requests_to_vet': nr_commentary_page_requests_to_vet, 
                   'nr_comments_to_vet': nr_comments_to_vet, 
                   'nr_thesislink_requests_to_vet': nr_thesislink_requests_to_vet, 
                   'nr_authorship_claims_to_vet': nr_authorship_claims_to_vet,
                   'nr_reports_to_vet': nr_reports_to_vet, 
                   'nr_submissions_to_assign': nr_submissions_to_assign, 
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
                   'lists_owned': lists_owned,
                   'lists': lists,
                   'teams_led': teams_led,
                   'teams': teams,
                   'graphs_owned': graphs_owned,
                   'graphs_private': graphs_private,
                   }
        return render(request, 'scipost/personal_page.html', context)
    else:
        form = AuthenticationForm()
        context = {'form': form}
        return render(request, 'scipost/login.html', context)


@login_required
def change_password(request):
#    if not request.user.is_authenticated:
#        form = AuthenticationForm()
#        return render(request, 'scipost/login.html', {'form': form})
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            if not request.user.check_password(form.cleaned_data['password_prev']):
                return render(request, 'scipost/change_password.html', 
                              {'form': form, 'errormessage': 'The currently existing password you entered is incorrect'})
            if form.cleaned_data['password_new'] != form.cleaned_data['password_verif']:
                return render(request, 'scipost/change_password.html', 
                              {'form': form, 'errormessage': 'Your new password entries must match'})
            request.user.set_password(form.cleaned_data['password_new'])
            request.user.save()
            ack = True
        context = {'ack': True, 'form': form}
    else:
        form = PasswordChangeForm()
        context = {'ack': False, 'form': form}
    return render (request, 'scipost/change_password.html', context)


def reset_password_confirm(request, uidb64=None, token=None):
    return password_reset_confirm(request, template_name='scipost/reset_password_confirm.html',
                                  uidb64=uidb64, token=token, post_reset_redirect=reverse('scipost:login'))

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
            request.user.last_name = user_form.cleaned_data['last_name']
            request.user.contributor.title = cont_form.cleaned_data['title']
            request.user.contributor.orcid_id = cont_form.cleaned_data['orcid_id']
            request.user.contributor.country_of_employment = cont_form.cleaned_data['country_of_employment']
            request.user.contributor.address = cont_form.cleaned_data['address']
            request.user.contributor.affiliation = cont_form.cleaned_data['affiliation']
            request.user.contributor.personalwebpage = cont_form.cleaned_data['personalwebpage']
            request.user.save()
            request.user.contributor.save()
            return render(request, 'scipost/update_personal_data_ack.html')
    else:
        user_form = UpdateUserDataForm(instance=contributor.user)
        cont_form = UpdatePersonalDataForm(instance=contributor)
    return render(request, 'scipost/update_personal_data.html', {'user_form': user_form, 'cont_form': cont_form})


@login_required
def claim_authorships(request):
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
        submission = get_object_or_404(Submission,pk=submission_id)
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
        commentary = get_object_or_404(Commentary,pk=commentary_id)
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
        thesislink = get_object_or_404(ThesisLink,pk=thesis_id)
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


@login_required
def contributor_info(request, contributor_id):
    contributor = Contributor.objects.get(pk=contributor_id)
    contributor_submissions = Submission.objects.filter(authors__in=[contributor])
    contributor_commentaries = Commentary.objects.filter(authors__in=[contributor])
    contributor_theses = ThesisLink.objects.filter(author_as_cont__in=[contributor])
    contributor_comments = (Comment.objects
                            .filter(author=contributor, is_author_reply=False, status__gte=1)
                            .order_by('-date_submitted'))
    contributor_authorreplies = (Comment.objects
                                 .filter(author=contributor, is_author_reply=True, status__gte=1)
                                 .order_by('-date_submitted'))
    context = {'contributor': contributor, 
               'contributor_submissions': contributor_submissions,
               'contributor_commentaries': contributor_commentaries,
               'contributor_theses': contributor_theses,
               'contributor_comments': contributor_comments, 
               'contributor_authorreplies': contributor_authorreplies}
    return render(request, 'scipost/contributor_info.html', context)


#####################
# Editorial College #
#####################


def EdCol_bylaws(request):
    return render(request, 'scipost/EdCol_by-laws.html')


#########
# Lists #
#########

@permission_required('scipost.add_list', return_403=True)
def create_list(request):
    listcreated = False
    message = None
    if request.method == "POST":
        create_list_form = CreateListForm(request.POST)
        if create_list_form.is_valid():
            newlist = List(owner=request.user.contributor,
                           title=create_list_form.cleaned_data['title'],
                           description=create_list_form.cleaned_data['description'],
                           private=create_list_form.cleaned_data['private'],
                           created=timezone.now())
            newlist.save()
            listcreated = True
            assign_perm('scipost.change_list', request.user, newlist)
            assign_perm('scipost.view_list', request.user, newlist)
            assign_perm('scipost.delete_list', request.user, newlist)
            message = 'List ' + create_list_form.cleaned_data['title'] + ' was successfully created.'
    else:
        create_list_form = CreateListForm()
    context = {'create_list_form': create_list_form, 'listcreated': listcreated, 
               'message': message}
    return render(request, 'scipost/create_list.html', context)


@permission_required_or_403('scipost.view_list', (List, 'id', 'list_id'))
def list(request, list_id):
    list = get_object_or_404(List, pk=list_id)
    context = {'list': list}
    if request.method == "POST":
        search_for_list_form = SearchForm(request.POST)
        if search_for_list_form.is_valid():
            context.update(documentsSearchResults(search_for_list_form.cleaned_data['query']))
    else:
        search_for_list_form = SearchForm()
    context.update({'search_for_list_form': search_for_list_form})
    return render(request, 'scipost/list.html', context)


@permission_required_or_403('scipost.change_list', (List, 'id', 'list_id'))
def list_add_element(request, list_id, type, element_id):
    list = get_object_or_404(List, pk=list_id)
    if type == 'C':
        commentary = get_object_or_404(Commentary, pk=element_id)
        list.commentaries.add(commentary)
    elif type == 'S':
        submission = get_object_or_404(Submission, pk=element_id)
        list.submissions.add(submission)
    elif type == 'T':
        thesislink = get_object_or_404(ThesisLink, pk=element_id)
        list.thesislinks.add(thesislink)
    elif type == 'c':
        comment = get_object_or_404(Comment, pk=element_id)
        list.comments.add(comment)
    return redirect(reverse('scipost:list', kwargs={'list_id': list_id}))


@permission_required_or_403('scipost.change_list', (List, 'id', 'list_id'))
def list_remove_element(request, list_id, type, element_id):
    list = get_object_or_404(List, pk=list_id)
    if type == 'C':
        commentary = get_object_or_404(Commentary, pk=element_id)
        list.commentaries.remove(commentary)
    elif type == 'S':
        submission = get_object_or_404(Submission, pk=element_id)
        list.submissions.remove(submission)
    elif type == 'T':
        thesislink = get_object_or_404(ThesisLink, pk=element_id)
        list.thesislinks.remove(thesislink)
    elif type == 'c':
        comment = get_object_or_404(Comment, pk=element_id)
        list.comments.remove(comment)
    return redirect(reverse('scipost:list', kwargs={'list_id': list_id}))


#########
# Teams #
#########

@permission_required('scipost.add_team', return_403=True)
def create_team(request):
    if request.method == "POST":
        create_team_form = CreateTeamForm(request.POST)
        if create_team_form.is_valid():
            newteam = Team(leader=request.user.contributor,
                           name=create_team_form.cleaned_data['name'],
                           established=timezone.now())
            newteam.save()
            assign_perm('scipost.change_team', request.user, newteam)
            assign_perm('scipost.view_team', request.user, newteam)
            assign_perm('scipost.delete_team', request.user, newteam)
            return redirect(reverse('scipost:add_team_member', kwargs={'team_id': newteam.id}))
    else:
        create_team_form = CreateTeamForm()
    add_team_member_form = AddTeamMemberForm()
    context = {'create_team_form': create_team_form, 
               'add_team_member_form': add_team_member_form}
    return render(request, 'scipost/create_team.html', context)

@permission_required_or_403('scipost.change_team', (Team, 'id', 'team_id'))
def add_team_member(request, team_id, contributor_id=None):
    team = get_object_or_404(Team, pk=team_id)
    contributors_found = None
    if contributor_id is not None:
        contributor = get_object_or_404(Contributor, pk=contributor_id)
        team.members.add(contributor)
        team.save()
        assign_perm('scipost.view_team', contributor.user, team)
        return redirect(reverse('scipost:add_team_member', kwargs={'team_id': team_id}))
    if request.method == "POST":
        add_team_member_form = AddTeamMemberForm(request.POST)
        if add_team_member_form.is_valid():
            contributors_found = Contributor.objects.filter(user__last_name__icontains=add_team_member_form.cleaned_data['last_name'])
    else:
        add_team_member_form = AddTeamMemberForm()
    context = {'team': team, 'add_team_member_form': add_team_member_form,
               'contributors_found': contributors_found}
    return render(request, 'scipost/add_team_member.html', context)


##########
# Graphs #
##########

@permission_required('scipost.add_graph', return_403=True)
def create_graph(request):
    graphcreated = False
    message = None
    if request.method == "POST":
        create_graph_form = CreateGraphForm(request.POST)
        if create_graph_form.is_valid():
            newgraph = Graph(owner=request.user.contributor,
                             title=create_graph_form.cleaned_data['title'],
                             description=create_graph_form.cleaned_data['description'],
                             private=create_graph_form.cleaned_data['private'],
                             created=timezone.now())
            newgraph.save()
            assign_perm('scipost.change_graph', request.user, newgraph)
            assign_perm('scipost.view_graph', request.user, newgraph)
            assign_perm('scipost.delete_graph', request.user, newgraph)
            graphcreated = True
            message = 'Graph ' + create_graph_form.cleaned_data['title'] + ' was successfully created.'
    else:
        create_graph_form = CreateGraphForm()
    context = {'create_graph_form': create_graph_form, 'graphcreated': graphcreated,
               'message': message}
    return render(request, 'scipost/create_graph.html', context)


@permission_required_or_403('scipost.view_graph', (Graph, 'id', 'graph_id'))
def graph(request, graph_id):
    graph = get_object_or_404(Graph, pk=graph_id)
    nodes = Node.objects.filter(graph=graph)
    arcs = Arc.objects.filter(graph=graph)
    if request.method == "POST":
        attach_teams_form = ManageTeamsForm(request.POST, 
                                            contributor=request.user.contributor, 
                                            initial={'teams_with_access': graph.teams_with_access.all()}
                                            )
        create_node_form = CreateNodeForm(request.POST)
        create_arc_form = CreateArcForm(request.POST, graph=graph)
        if attach_teams_form.has_changed() and attach_teams_form.is_valid():
            graph.teams_with_access = attach_teams_form.cleaned_data['teams_with_access']
            graph.save()
        elif create_node_form.has_changed() and create_node_form.is_valid():
            newnode = Node(graph=graph, 
                           added_by=request.user.contributor,
                           created=timezone.now(),
                           name=create_node_form.cleaned_data['name'],
                           description=create_node_form.cleaned_data['description'])
            newnode.save()
        elif create_arc_form.has_changed() and create_arc_form.is_valid():
            sourcenode = create_arc_form.cleaned_data['source']
            targetnode = create_arc_form.cleaned_data['target']
            if sourcenode != targetnode:
                newarc = Arc(graph=graph,
                             added_by=request.user.contributor,
                             created=timezone.now(),
                             source=sourcenode,
                             target=targetnode,
                             length=create_arc_form.cleaned_data['length']
                             )
                newarc.save()            
    else:
        attach_teams_form = ManageTeamsForm(contributor=request.user.contributor, 
                                            initial={'teams_with_access': graph.teams_with_access.all()}
                                            )
        create_node_form = CreateNodeForm()
        create_arc_form = CreateArcForm(graph=graph)
    context = {'graph': graph, 'nodes': nodes, 
               'attach_teams_form': attach_teams_form,
               'create_node_form': create_node_form,
               'create_arc_form': create_arc_form}
    return render(request, 'scipost/graph.html', context)


def edit_graph_node(request, node_id):
    node = get_object_or_404(Node, pk=node_id)
    errormessage = ''
    if not request.user.has_perm('scipost.change_graph', node.graph):
        errormessage = 'You do not have permission to edit this graph.'
    elif request.method == "POST":
        edit_node_form = CreateNodeForm(request.POST, instance=node)
        if edit_node_form.is_valid():
            node.name=edit_node_form.cleaned_data['name']
            node.description=edit_node_form.cleaned_data['description']
            node.save()
            create_node_form = CreateNodeForm()
            create_arc_form = CreateArcForm(graph=node.graph)
            context =  {'create_node_form': create_node_form,
                        'create_arc_form': create_arc_form}
            return redirect(reverse('scipost:graph', kwargs={'graph_id': node.graph.id}), context)
    else:
        edit_node_form = CreateNodeForm(instance=node)
    context = {'graph': graph, 'node': node, 'edit_node_form': edit_node_form,
               'errormessage': errormessage}
    return render(request, 'scipost/edit_graph_node.html', context)


def delete_graph_node(request, node_id):
    node = get_object_or_404(Node, pk=node_id)
    errormessage = ''
    if not request.user.has_perm('scipost.change_graph', node.graph):
        raise PermissionDenied
    else:
        # Remove all the graph arcs 
        Arc.objects.filter(source=node).delete()
        Arc.objects.filter(target=node).delete()
        # Delete node itself
        node.delete()
    return redirect(reverse('scipost:graph', kwargs={'graph_id': node.graph.id}))


@permission_required_or_403('scipost.view_graph', (Graph, 'id', 'graph_id'))
def api_graph(request, graph_id):
    """ Produce JSON data to plot graph """
    graph = get_object_or_404(Graph, pk=graph_id)
    nodes = Node.objects.filter(graph=graph)
    arcs = Arc.objects.filter(graph=graph)
    nodesjson = []
    arcsjson = []
    for node in nodes:
        nodesjson.append({'name': node.name, 'id': node.id})
#        for origin in node.arcs_in.all():
#            links.append({'source': origin.name, 'source_id': origin.id, 
#                          'target': node.name, 'target_id': node.id})
    for arc in arcs:
        arcsjson.append({'id': arc.id,
                         'source': arc.source.name, 'source_id': arc.source.id,
                         'target': arc.target.name, 'target_id': arc.target.id,
                         'length': arc.length})
    return JsonResponse({'nodes': nodesjson, 'arcs': arcsjson}, safe=False)
