import datetime
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.db.models import Avg

from .models import *
from .forms import *

from commentaries.models import Commentary
from comments.models import Comment, AuthorReply
from submissions.models import Submission, Report


#############
# Main view
#############

def index(request):
    return render(request, 'scipost/index.html')


###############
# Information
###############

def base(request):
    return render(request, 'scipost/base.html')

def about(request):
    return render(request, 'scipost/about.html')

def description(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="SciPost_Description.pdf"'
    return response

def peer_witnessed_refereeing(request):
    return render(request, 'scipost/peer_witnessed_refereeing.html')


################
# Contributors:
################

title_dict = dict(TITLE_CHOICES)
reg_ref_dict = dict(REGISTRATION_REFUSAL_CHOICES)

def register(request):
    # If POST, process the form data
    if request.method == 'POST':
        # create a form instance and populate it with the form data
        form = RegistrationForm(request.POST)
        # check whether it's valid
        if form.is_valid():
            # check for mismatching passwords
            if form.cleaned_data['password'] != form.cleaned_data['password_verif']:
                return render(request, 'scipost/register.html', {'form': form, 'errormessage': 'Your passwords must match'})
            # check for already-existing username
            if User.objects.filter(username=form.cleaned_data['username']).exists():
                return render(request, 'scipost/register.html', {'form': form, 'errormessage': 'This username is already in use'})                
            # create the user
            user = User.objects.create_user (
                first_name = form.cleaned_data['first_name'],
                last_name = form.cleaned_data['last_name'],
                email = form.cleaned_data['email'],
                username = form.cleaned_data['username'],
                password = form.cleaned_data['password']
                )
            contributor = Contributor (
                user=user, 
                title = form.cleaned_data['title'],
                orcid_id = form.cleaned_data['orcid_id'],
                address = form.cleaned_data['address'],
                affiliation = form.cleaned_data['affiliation'],
                personalwebpage = form.cleaned_data['personalwebpage'],
                )
            contributor.save()
            email_text = 'Dear ' + title_dict[contributor.title] + ' ' + contributor.user.last_name + ', \n\nYour request for registration to the SciPost publication portal has been received, and will be processed soon. Many thanks for your interest.  \n\nThe SciPost Team.'
            emailmessage = EmailMessage('SciPost registration request received', email_text, 'registration@scipost.org', [contributor.user.email, 'registration@scipost.org'], reply_to=['registration@scipost.org'])
            emailmessage.send(fail_silently=False)
            return HttpResponseRedirect('thanks_for_registering')
    # if GET or other method, create a blank form
    else:
        form = RegistrationForm()

    errormessage = ''
    return render(request, 'scipost/register.html', {'form': form, 'errormessage': errormessage})


def thanks_for_registering(request):
    return render(request, 'scipost/thanks_for_registering.html')


def vet_registration_requests(request):
    contributor = Contributor.objects.get(user=request.user)
    registration_requests_to_vet = Contributor.objects.filter(rank=0)
    form = VetRegistrationForm()
    context = {'contributor': contributor, 'registration_requests_to_vet': registration_requests_to_vet, 'form': form }
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
                email_text = 'Dear ' + title_dict[contributor.title] + ' ' + contributor.user.last_name + ', \n\nYour registration to the SciPost publication portal has been accepted. You can now login and contribute. \n\nThe SciPost Team.'
                emailmessage = EmailMessage('SciPost registration accepted', email_text, 'registration@scipost.org', [contributor.user.email, 'registration@scipost.org'], reply_to=['registration@scipost.org'])
                emailmessage.send(fail_silently=False)
            else:
                ref_reason = int(form.cleaned_data['refusal_reason'])
                email_text = 'Dear ' + title_dict[contributor.title] + ' ' + contributor.user.last_name + ', \n\nYour registration to the SciPost publication portal has been turned down, the reason being: ' + reg_ref_dict[ref_reason] + '. You can however still view all SciPost contents, just not submit papers, comments or votes. We nonetheless thank you for your interest. \n\nThe SciPost Team.'
                if form.cleaned_data['email_response_field']:
                    email_text += '\n\nFurther explanations: ' + form.cleaned_data['email_response_field']
                emailmessage = EmailMessage('SciPost registration: unsuccessful', email_text, 'registration@scipost.org', [contributor.user.email, 'registration@scipost.org'], reply_to=['registration@scipost.org'])
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
                return render(request, 'scipost/personal_page.html', context)
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
        nr_submissions_to_process = 0
        if contributor.rank >= 4:
            # count the number of pending registration request
            nr_reg_to_vet = Contributor.objects.filter(rank=0).count()
            nr_submissions_to_process = Submission.objects.filter(vetted=False).count()
        nr_commentary_page_requests_to_vet = 0
        nr_comments_to_vet = 0
        nr_author_replies_to_vet = 0
        nr_reports_to_vet = 0
        if contributor.rank >= 2:
            nr_commentary_page_requests_to_vet = Commentary.objects.filter(vetted=False).count()
            nr_comments_to_vet = Comment.objects.filter(status=0).count()
            nr_author_replies_to_vet = AuthorReply.objects.filter(status=0).count()
            nr_reports_to_vet = Report.objects.filter(status=0).count()
        context = {'contributor': contributor, 'nr_reg_to_vet': nr_reg_to_vet, 'nr_commentary_page_requests_to_vet': nr_commentary_page_requests_to_vet, 'nr_comments_to_vet': nr_comments_to_vet, 'nr_author_replies_to_vet': nr_author_replies_to_vet, 'nr_reports_to_vet': nr_reports_to_vet, 'nr_submissions_to_process': nr_submissions_to_process }
        return render(request, 'scipost/personal_page.html', context)
    else:
        form = AuthenticationForm()
        context = {'form': form}
        return render(request, 'scipost/login.html', context)


def change_password(request):
    if request.user.is_authenticated and request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            # verify existing password:
            if not request.user.check_password(form.cleaned_data['password_prev']):
                return render(request, 'scipost/change_password.html', {'form': form, 'errormessage': 'The currently existing password you entered is incorrect'})
            # check for mismatching new passwords
            if form.cleaned_data['password_new'] != form.cleaned_data['password_verif']:
                return render(request, 'scipost/change_password.html', {'form': form, 'errormessage': 'Your new password entries must match'})
            # otherwise simply change the pwd:
            request.user.set_password(form.cleaned_data['password_new'])
            request.user.save()
            return render(request, 'scipost/change_password_ack.html')
    else:
        form = PasswordChangeForm()
    return render (request, 'scipost/change_password.html', {'form': form})


def change_password_ack(request):
    return render (request, 'scipost/change_password_ack.html')


def update_personal_data(request):
    if request.user.is_authenticated:
        contributor = Contributor.objects.get(user=request.user)
        if request.method == 'POST':
            form = UpdatePersonalDataForm(request.POST)
            if form.is_valid():
                request.user.email = form.cleaned_data['email']
                request.user.first_name = form.cleaned_data['first_name']
                request.user.last_name = form.cleaned_data['last_name']
                request.user.contributor.title = form.cleaned_data['title']
                request.user.contributor.orcid = form.cleaned_data['orcid_id']
                request.user.contributor.address = form.cleaned_data['address']
                request.user.contributor.affiliation = form.cleaned_data['affiliation']
                request.user.contributor.personalwebpage = form.cleaned_data['personalwebpage']
                request.user.save()
                request.user.contributor.save()
                return render(request, 'scipost/update_personal_data_ack.html')
        else:
            #form = UpdatePersonalDataForm()
            aff = contributor.affiliation
            prefilldata = {'affiliation': aff}
            form = UpdatePersonalDataForm(initial=prefilldata)
            return render(request, 'scipost/update_personal_data.html', {'form': form, 'contributor': contributor})
    else:
        form = AuthenticationForm()
        return render(request, 'scipost/login.html', {'form': form})


def update_personal_data_ack(request):
    return render (request, 'scipost/update_personal_data_ack.html')

