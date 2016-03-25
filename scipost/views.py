import datetime
import hashlib
import random
import string

from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.views import password_reset, password_reset_confirm
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.db.models import Avg


from .models import *
from .forms import *

from .global_methods import *
from .utils import *


from commentaries.models import Commentary
from commentaries.forms import CommentarySearchForm
from comments.models import Comment
from submissions.models import Submission, Report
from submissions.forms import SubmissionSearchForm
from theses.models import ThesisLink
from theses.forms import ThesisLinkSearchForm


#############
# Main view
#############

def index(request):
    submission_search_form = SubmissionSearchForm(request.POST)
    commentary_search_form = CommentarySearchForm(request.POST)
    thesislink_search_form = ThesisLinkSearchForm(request.POST)
    context = {'submission_search_form': submission_search_form, 
               'commentary_search_form': commentary_search_form, 
               'thesislink_search_form': thesislink_search_form}
    return render(request, 'scipost/index.html', context)

###############
# Information
###############

def base(request):
    return render(request, 'scipost/base.html')

def description(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="SciPost_Description.pdf"'
    return response


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
            Utils.create_and_save_contributor()
            Utils.send_registration_email()
            return HttpResponseRedirect('thanks_for_registering')
    else:
        form = RegistrationForm()
    errormessage = ''
    return render(request, 'scipost/register.html', {'form': form, 'errormessage': errormessage})



def activation(request, key):
    activation_expired = False
    already_active = False
    contributor = get_object_or_404(Contributor, activation_key=key)
    if contributor.user.is_active == False:
        if timezone.now() > contributor.key_expires:
            activation_expired = True
            id_user = contributor.user.id
            context = {'oldkey': key}
            return render(request, 'scipost/request_new_activation_link.html', context)
        else: 
            contributor.user.is_active = True
            contributor.user.save()
            return render(request, 'scipost/activation_ack.html')
    else:
        already_active = True
        return render(request, 'scipost/already_activated.html')
    # will never come beyond here
    return render(request, 'scipost/index.html')



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
    emailmessage = EmailMessage('SciPost registration: new email activation link', email_text, 'registration@scipost.org', 
                                [contributor.user.email, 'registration@scipost.org'], reply_to=['registration@scipost.org'])
    emailmessage.send(fail_silently=False)
    return render (request, 'scipost/request_new_activation_link_ack.html')



def vet_registration_requests(request):
    contributor = Contributor.objects.get(user=request.user)
    #contributor_to_vet = Contributor.objects.filter(user__is_active=True, rank=0).first() # limit to one at a time
    contributors_to_vet = Contributor.objects.filter(user__is_active=True, rank=0).order_by('key_expires')
    form = VetRegistrationForm()
    #context = {'contributor_to_vet': contributor_to_vet, 'form': form }
    context = {'contributors_to_vet': contributors_to_vet, 'form': form }
    return render(request, 'scipost/vet_registration_requests.html', context)


def vet_registration_request_ack(request, contributor_id):
    # process the form
    if request.method == 'POST':
        form = VetRegistrationForm(request.POST)
        contributor = Contributor.objects.get(pk=contributor_id)
        if form.is_valid():
            if form.cleaned_data['promote_to_rank_1']:
                contributor.rank = 1
                contributor.save()
                email_text = ('Dear ' + title_dict[contributor.title] + ' ' + contributor.user.last_name + 
                              ', \n\nYour registration to the SciPost publication portal has been accepted. ' +
                              'You can now login and contribute. \n\nThe SciPost Team.')
                emailmessage = EmailMessage('SciPost registration accepted', email_text, 'registration@scipost.org', 
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
                emailmessage = EmailMessage('SciPost registration: unsuccessful', email_text, 'registration@scipost.org', 
                                            [contributor.user.email, 'registration@scipost.org'], reply_to=['registration@scipost.org'])
                emailmessage.send(fail_silently=False)
                contributor.rank = form.cleaned_data['refusal_reason']
                contributor.save()

    context = {}
    return render(request, 'scipost/vet_registration_request_ack.html', context)


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None and user.contributor.rank > 0:
            if user.is_active:
                login(request, user)
                contributor = Contributor.objects.get(user=request.user)
                context = {'contributor': contributor }
                #return render(request, 'scipost/personal_page.html', context)
                return HttpResponseRedirect('/personal_page')
            else:
                return render(request, 'scipost/disabled_account.html')
        else:
            return render(request, 'scipost/login_error.html')
    else:
        form = AuthenticationForm()
        return render(request, 'scipost/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return render(request, 'scipost/logout.html')


def personal_page(request):
    if request.user.is_authenticated():
        contributor = Contributor.objects.get(user=request.user)
        # if an editor, count the number of actions required:
        nr_reg_to_vet = 0
        nr_reg_awaiting_validation = 0
        nr_submissions_to_process = 0
        if contributor.rank >= 4:
            now = timezone.now()
            intwodays = now + timezone.timedelta(days=2)
            # count the number of pending registration request
            nr_reg_to_vet = Contributor.objects.filter(user__is_active=True, rank=0).count()
            nr_reg_awaiting_validation = Contributor.objects.filter(
                user__is_active=False, key_expires__gte=now, key_expires__lte=intwodays, rank=0
                ).count()
            nr_submissions_to_process = Submission.objects.filter(vetted=False).count()
        nr_commentary_page_requests_to_vet = 0
        nr_comments_to_vet = 0
        nr_reports_to_vet = 0
        nr_thesislink_requests_to_vet = 0
        nr_authorship_claims_to_vet = 0
        if contributor.rank >= 2:
            nr_commentary_page_requests_to_vet = Commentary.objects.filter(vetted=False).count()
            nr_comments_to_vet = Comment.objects.filter(status=0).count()
            nr_reports_to_vet = Report.objects.filter(status=0).count()
            nr_thesislink_requests_to_vet = ThesisLink.objects.filter(vetted=False).count()
            nr_authorship_claims_to_vet = AuthorshipClaim.objects.filter(status='0').count()
        # Verify if there exist objects authored by this contributor, whose authorship hasn't been claimed yet
        own_submissions = Submission.objects.filter(authors__in=[contributor])
        own_commentaries = Commentary.objects.filter(authors__in=[contributor])
        nr_submission_authorships_to_claim = Submission.objects.filter(author_list__contains=contributor.user.last_name).exclude(authors__in=[contributor]).exclude(authors_claims__in=[contributor]).exclude(authors_false_claims__in=[contributor]).count()
        nr_commentary_authorships_to_claim = Commentary.objects.filter(author_list__contains=contributor.user.last_name).exclude(authors__in=[contributor]).exclude(authors_claims__in=[contributor]).exclude(authors_false_claims__in=[contributor]).count()
        own_comments = Comment.objects.filter(author=contributor,is_author_reply=False).order_by('-date_submitted')
        own_authorreplies = Comment.objects.filter(author=contributor,is_author_reply=True).order_by('-date_submitted')
        context = {'contributor': contributor, 'nr_reg_to_vet': nr_reg_to_vet, 
                   'nr_reg_awaiting_validation': nr_reg_awaiting_validation, 
                   'nr_commentary_page_requests_to_vet': nr_commentary_page_requests_to_vet, 
                   'nr_comments_to_vet': nr_comments_to_vet, 
                   'nr_reports_to_vet': nr_reports_to_vet, 
                   'nr_submissions_to_process': nr_submissions_to_process, 
                   'nr_thesislink_requests_to_vet': nr_thesislink_requests_to_vet, 
                   'nr_authorship_claims_to_vet': nr_authorship_claims_to_vet,
                   'nr_submission_authorships_to_claim': nr_submission_authorships_to_claim,
                   'nr_commentary_authorships_to_claim': nr_commentary_authorships_to_claim,
                   'own_submissions': own_submissions, 'own_commentaries': own_commentaries,
                   'own_comments': own_comments, 'own_authorreplies': own_authorreplies}
        return render(request, 'scipost/personal_page.html', context)
    else:
        form = AuthenticationForm()
        context = {'form': form}
        return render(request, 'scipost/login.html', context)


def change_password(request):
    if request.user.is_authenticated and request.method == 'POST':
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


def update_personal_data(request):
    if request.user.is_authenticated:
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
    else:
        form = AuthenticationForm()
        return render(request, 'scipost/login.html', {'form': form})


def claim_authorships(request):
    if request.user.is_authenticated:
       contributor = Contributor.objects.get(user=request.user)

       submission_authorships_to_claim = Submission.objects.filter(author_list__contains=contributor.user.last_name).exclude(authors__in=[contributor]).exclude(authors_claims__in=[contributor]).exclude(authors_false_claims__in=[contributor])
       sub_auth_claim_form = AuthorshipClaimForm()
       commentary_authorships_to_claim = Commentary.objects.filter(author_list__contains=contributor.user.last_name).exclude(authors__in=[contributor]).exclude(authors_claims__in=[contributor]).exclude(authors_false_claims__in=[contributor])
       com_auth_claim_form = AuthorshipClaimForm()

       context = {'submission_authorships_to_claim': submission_authorships_to_claim,
                  'sub_auth_claim_form': sub_auth_claim_form,
                  'commentary_authorships_to_claim': commentary_authorships_to_claim,
                  'com_auth_claim_form': com_auth_claim_form,}
       return render(request, 'scipost/claim_authorships.html', context)
    else:
        form = AuthenticationForm()
        return render(request, 'scipost/login.html', {'form': form})


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
    return render(request, 'scipost/claim_authorships.html')

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
    return render(request, 'scipost/claim_authorships.html')


def vet_authorship_claims(request):
    contributor = Contributor.objects.get(user=request.user)
    claims_to_vet = AuthorshipClaim.objects.filter(status='0')
    context = {'claims_to_vet': claims_to_vet }
    return render(request, 'scipost/vet_authorship_claims.html', context)

def vet_sub_authorship_claim(request, submission_id, claim):
    if request.method == 'POST':
        contributor = Contributor.objects.get(user=request.user)
        submission = Submission.objects.get(pk=submission_id)
        submission.authors_claims.remove(contributor)
        claim_to_vet = AuthorshipClaim.objects.get(claimant=contributor, submission=submission)
        if claim == '1':
            submission.authors.add(contributor)
            claim_to_vet.status = '1'
        elif claim == '0':
            submission.authors_false_claims.add(contributor)
            claim_to_vet.status = '-1'
        submission.save()
        claim_to_vet.save()
    return render(request, 'scipost/claim_authorships.html')

def vet_com_authorship_claim(request, commentary_id, claim):
    if request.method == 'POST':
        contributor = Contributor.objects.get(user=request.user)
        commentary = Commentary.objects.get(pk=commentary_id)
        commentary.authors_claims.remove(contributor)
        claim_to_vet = AuthorshipClaim.objects.get(claimant=contributor, commentary=commentary)
        if claim == '1':
            commentary.authors.add(contributor)
        elif claim == '0':
            commentary.authors_false_claims.add(contributor)
        claim_to_vet.status = claim
        commentary.save()
        claim_to_vet.save()
    return render(request, 'scipost/claim_authorships.html')



def contributor_info(request, contributor_id):
    if request.user.is_authenticated():
        contributor = Contributor.objects.get(pk=contributor_id)
        contributor_comments = Comment.objects.filter(author=contributor, is_author_reply=False, status__gte=1).order_by('-date_submitted')
        contributor_authorreplies = Comment.objects.filter(author=contributor, is_author_reply=True, status__gte=1).order_by('-date_submitted')
        context = {'contributor': contributor, 
                   'contributor_comments': contributor_comments, 
                   'contributor_authorreplies': contributor_authorreplies}
        return render(request, 'scipost/contributor_info.html', context)
    else:
        form = AuthenticationForm()
        context = {'form': form}
        return render(request, 'scipost/login.html', context)

