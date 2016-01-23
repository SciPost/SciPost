import datetime
import hashlib
import random
import string

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
    if request.user.is_authenticated():
        return HttpResponseRedirect('personal_page')
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
            # Set to inactive until activation via email link
            user.is_active = False 
            user.save()
            contributor = Contributor (
                user=user, 
                title = form.cleaned_data['title'],
                orcid_id = form.cleaned_data['orcid_id'],
                nationality = form.cleaned_data['nationality'],
                country_of_employment = form.cleaned_data['country_of_employment'],
                address = form.cleaned_data['address'],
                affiliation = form.cleaned_data['affiliation'],
                personalwebpage = form.cleaned_data['personalwebpage'],
                )
            contributor.save()
            # Generate email activation key and link
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
            email_text = 'Dear ' + title_dict[contributor.title] + ' ' + contributor.user.last_name + ', \n\nYour request for registration to the SciPost publication portal has been received. You now need to validate your email by visiting this link within the next 48 hours: \n\n' + 'https://scipost.org/activation/' + contributor.activation_key + '\n\nYour registration will thereafter be vetted. Many thanks for your interest.  \n\nThe SciPost Team.'
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


def activation_ack(request):
    return render(request, 'scipost/activation_ack.html')


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
    email_text = 'Dear ' + title_dict[contributor.title] + ' ' + contributor.user.last_name + ', \n\nYour request for a new email activation link for registration to the SciPost publication portal has been received. You now need to visit this link within the next 48 hours: \n\n' + 'https://scipost.org/activation/' + contributor.activation_key + '\n\nYour registration will thereafter be vetted. Many thanks for your interest.  \n\nThe SciPost Team.'
    emailmessage = EmailMessage('SciPost registration: new email activation link', email_text, 'registration@scipost.org', [contributor.user.email, 'registration@scipost.org'], reply_to=['registration@scipost.org'])
    emailmessage.send(fail_silently=False)
    return render (request, 'scipost/request_new_activation_link_ack.html')


def request_new_activation_link_ack(request):
    return render (request, 'scipost/request_new_activation_link_ack.html')


def already_activated(request):
    return render (request, 'scipost/already_activated.html')


def vet_registration_requests(request):
    contributor = Contributor.objects.get(user=request.user)
    contributor_to_vet = Contributor.objects.filter(user__is_active=True, rank=0).first() # limit to one at a time
    if contributor_to_vet is not None:
        form = VetRegistrationForm()
        context = {'contributor': contributor, 'contributor_to_vet': contributor_to_vet, 'form': form }
        return render(request, 'scipost/vet_registration_requests.html', context)
    return render (request, 'scipost/no_registration_req_to_vet.html')


def no_registration_req_to_vet(request):
    return render(request, 'scipost/no_registration_req_to_vet.html')

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
        nr_reg_awaiting_validation = 0
        nr_submissions_to_process = 0
        if contributor.rank >= 4:
            now = timezone.now()
            intwodays = now + timezone.timedelta(days=2)
            # count the number of pending registration request
            nr_reg_to_vet = Contributor.objects.filter(user__is_active=True, rank=0).count()
            nr_reg_awaiting_validation = Contributor.objects.filter(user__is_active=False, key_expires__gte=now, key_expires__lte=intwodays, rank=0).count()
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
        context = {'contributor': contributor, 'nr_reg_to_vet': nr_reg_to_vet, 'nr_reg_awaiting_validation': nr_reg_awaiting_validation, 'nr_commentary_page_requests_to_vet': nr_commentary_page_requests_to_vet, 'nr_comments_to_vet': nr_comments_to_vet, 'nr_author_replies_to_vet': nr_author_replies_to_vet, 'nr_reports_to_vet': nr_reports_to_vet, 'nr_submissions_to_process': nr_submissions_to_process }
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
            user_form = UpdateUserDataForm(request.POST)
            cont_form = UpdatePersonalDataForm(request.POST)
            if user_form.is_valid() and cont_form.is_valid():
                request.user.email = user_form.cleaned_data['email']
                request.user.first_name = user_form.cleaned_data['first_name']
                request.user.last_name = user_form.cleaned_data['last_name']
                request.user.contributor.title = cont_form.cleaned_data['title']
                request.user.contributor.orcid_id = cont_form.cleaned_data['orcid_id']
                request.user.contributor.nationality = cont_form.cleaned_data['nationality']
                request.user.contributor.country_of_employment = cont_form.cleaned_data['country_of_employment']
                #request.user.contributor.address = cont_form.cleaned_data['address']
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


def update_personal_data_ack(request):
    return render (request, 'scipost/update_personal_data_ack.html')

