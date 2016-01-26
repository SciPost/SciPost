import datetime
import hashlib
import random
import string

from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.utils import timezone

from .models import *


class Utils(object):

    @classmethod
    def load(cls, dict):
        for var_name in dict:
            setattr(cls, var_name, dict[var_name])

    @classmethod
    def password_mismatch(cls):
        if cls.form.cleaned_data['password'] != cls.form.cleaned_data['password_verif']:
            return True
        else:
            return False

    @classmethod
    def username_already_taken(cls):
        if User.objects.filter(username=cls.form.cleaned_data['username']).exists():
            return True
        else:
            return False

    @classmethod
    def create_and_save_contributor(cls):
        user = User.objects.create_user (
            first_name = cls.form.cleaned_data['first_name'],
            last_name = cls.form.cleaned_data['last_name'],
            email = cls.form.cleaned_data['email'],
            username = cls.form.cleaned_data['username'],
            password = cls.form.cleaned_data['password']
            )
        # Set to inactive until activation via email link
        user.is_active = False
        user.save()
        contributor = Contributor (
            user=user,
            title = cls.form.cleaned_data['title'],
            orcid_id = cls.form.cleaned_data['orcid_id'],
            country_of_employment = cls.form.cleaned_data['country_of_employment'],
            address = cls.form.cleaned_data['address'],
            affiliation = cls.form.cleaned_data['affiliation'],
            personalwebpage = cls.form.cleaned_data['personalwebpage'],
            )
        contributor.save()
        Utils.load({'contributor': contributor})
        
    @classmethod
    def send_registration_email(cls):
        # Generate email activation key and link
        salt = ""
        for i in range(5):
            salt = salt + random.choice(string.ascii_letters)
        salt = salt.encode('utf8')
        usernamesalt = cls.contributor.user.username
        usernamesalt = usernamesalt.encode('utf8')
        cls.contributor.activation_key = hashlib.sha1(salt+usernamesalt).hexdigest()
        cls.contributor.key_expires = datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(days=2), "%Y-%m-%d %H:%M:%S")
        cls.contributor.save()
        email_text = 'Dear ' + title_dict[cls.contributor.title] + ' ' + cls.contributor.user.last_name + ', \n\nYour request for registration to the SciPost publication portal has been received. You now need to validate your email by visiting this link within the next 48 hours: \n\n' + 'https://scipost.org/activation/' + cls.contributor.activation_key + '\n\nYour registration will thereafter be vetted. Many thanks for your interest.  \n\nThe SciPost Team.'
        emailmessage = EmailMessage('SciPost registration request received', email_text, 'registration@scipost.org', [cls.contributor.user.email, 'registration@scipost.org'], reply_to=['registration@scipost.org'])
        emailmessage.send(fail_silently=False)
            

    
