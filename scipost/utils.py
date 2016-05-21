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
    def email_already_taken(cls):
        if User.objects.filter(email=cls.form.cleaned_data['email']).exists():
            return True
        else:
            return False

    @classmethod
    def email_already_invited(cls):
        if RegistrationInvitation.objects.filter(email=cls.form.cleaned_data['email']).exists():
            return True
        else:
            return False

    @classmethod
    def create_and_save_contributor(cls, invitation_key):
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
            invitation_key=invitation_key,
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
        cls.contributor.key_expires = datetime.datetime.strftime(
            datetime.datetime.now() + datetime.timedelta(days=2), "%Y-%m-%d %H:%M:%S")
        cls.contributor.save()
        email_text = ('Dear ' + title_dict[cls.contributor.title] + ' ' + 
                      cls.contributor.user.last_name + 
                      ', \n\nYour request for registration to the SciPost publication portal' +
                      ' has been received. You now need to validate your email by visiting ' +
                      'this link within the next 48 hours: \n\n' + 'https://scipost.org/activation/' + 
                      cls.contributor.activation_key + 
                      '\n\nYour registration will thereafter be vetted. Many thanks for your interest.  \n\nThe SciPost Team.')
        emailmessage = EmailMessage(
            'SciPost registration request received', email_text,
            'SciPost registration <registration@scipost.org>', 
            [cls.contributor.user.email],
            ['registration@scipost.org'],
            reply_to=['registration@scipost.org'])
        emailmessage.send(fail_silently=False)

        
    @classmethod
    def create_invitation(cls):
        invitation = RegistrationInvitation (
            title = cls.form.cleaned_data['title'],
            first_name = cls.form.cleaned_data['first_name'],
            last_name = cls.form.cleaned_data['last_name'],
            email = cls.form.cleaned_data['email'],
            invitation_type = cls.form.cleaned_data['invitation_type'],
            invited_by = cls.contributor,
            message_style = cls.form.cleaned_data['message_style'],
            personal_message = cls.form.cleaned_data['personal_message'],
            )
        Utils.load({'invitation': invitation})

    @classmethod
    def send_registration_invitation_email(cls):
        # Generate email activation key and link
        salt = ""
        for i in range(5):
            salt = salt + random.choice(string.ascii_letters)
        salt = salt.encode('utf8')
        invitationsalt = cls.invitation.last_name
        invitationsalt = invitationsalt.encode('utf8')
        cls.invitation.invitation_key = hashlib.sha1(salt+invitationsalt).hexdigest()
        cls.invitation.key_expires = datetime.datetime.strftime(
            datetime.datetime.now() + datetime.timedelta(days=14), "%Y-%m-%d %H:%M:%S")
        cls.invitation.save()
        email_text = ''
        if cls.invitation.invitation_type == 'F':
            email_text += 'RE: Invitation to join the Editorial College of SciPost\n\n'
        email_text += 'Dear '
        if cls.invitation.message_style == 'F':
            email_text += title_dict[cls.invitation.title] + ' ' + cls.invitation.last_name
        else:
            email_text += cls.invitation.first_name
        email_text +=  ',\n\n'
        if len(cls.invitation.personal_message) > 3:
            email_text += cls.invitation.personal_message + '\n\n'

        if cls.invitation.invitation_type == 'R':
            # Refereeing invitation
            # Details of the submission to referee are already in the personal_message field
            email_text += ('We would hereby like to cordially invite you to become a Contributor on SciPost ' +
                           '(our records show that you are not yet registered); ' +
                           'we have prepared a pre-filled form for you at\n\n' +
                           'https://scipost.org/invitation/' + cls.invitation.invitation_key + '\n\n' +
                           'after which your registration will be activated, allowing you to contribute, '
                           'in particular by providing referee reports.\n\n' +
                           'Many thanks in advance,\n\nThe SciPost Team')
            emailmessage = EmailMessage(
                'SciPost registration invitation', email_text,
                'SciPost Registration <registration@scipost.org>',
                [cls.invitation.email],
                ['registration@scipost.org'],
                reply_to=['registration@scipost.org'])

        else:
            email_text += ('You will have noticed that scientific publishing is currently undergoing many changes, and you will hopefully agree that it is of the utmost importance that the best interests of science and scientists be served by these developments. After much thinking and discussion about this issue, I recently decided to forge ahead and implement a new online publication portal by and for scientists.\n\nThe initiative, called SciPost, aims to build on the best traditions within our community (as exemplified by the arXiv.org preprint server) by offering a complete scientific publication platform, run by and for professional scientists, providing:\n\n' +
                           '- a means to comment on all existing literature;\n\n' +
                           "- a repository of links to theses (Habilitation, PhD, Master's);\n\n" +
                           '- and, most importantly, a collection of community-run two-way open access (no subscription fees, no author fees) journals with extremely stringent (peer-witnessed) refereeing.\n\n' +
                           'For the Journals, the main innovations are thus a redesigned, more accountable refereeing process (addressing some of the weaknesses identified in current systems and habits), together with a new concept for the editorial process, based on our Editorial College (exclusively composed of established, professionally practising scientists), designed to ensure the highest achievable scientific quality while minimizing the burden of the editorial workflow.\n\n')
            if cls.invitation.invitation_type == 'F':
                email_text += ('The SciPost.org portal has been intensively developed over the last few months. It is legally based on a not-for-profit foundation and will operate in perpetuity as a non-commercial entity at the exclusive service of the academic sector. We are now entering the next phase in the implementation, which is to build up the community of professional academics who will help operate it.\n\n' +
                               'To go straight to the point, on behalf of the foundation, I hereby have the honour to invite you to become an Editorial Fellow and thus join the Editorial College of SciPost Physics.\n\n' +
                               'Please note that only well-known and respected senior academics are being contacted for this purpose. Academic reputation and involvement in the community are the most important criteria guiding our considerations of who should belong to the Editorial College. We envision each subfield of physics to be represented by around a dozen Editorial Fellows.\n\n' +
                               "To help you in considering this, it would be best if you were to take the time to look at the website itself, which is anchored at scipost.org. Registration is now generally open, but you can also personally register (to become a Contributor, without necessarily committing to membership of the Editorial College, this to be discussed separately) by visiting the following single-use link, containing a partly pre-filled form for your convenience: \n\n" + 
                               'https://scipost.org/invitation/' + cls.invitation.invitation_key + '\n\n' +
                               'I will then activate your account. Many details about the initiative can then be found at scipost.org/about and at scipost.org/FAQ. Functioning of the College will proceed according to the by-laws set out in scipost.org/EdCol_by-laws.\n\n' +
                               "Since the success of this initiative is dependent on the involvement of the very people it is meant to serve, we'd be very grateful if you were to give due consideration to this proposal. We would expect you to commit just 2-4 hours per month to help perform Editorial duties; we will adjust the number of Editorial Fellows to ensure this is the case. You could try it out for 6 months or a year, and of course you could quit any time you wished. We'd be even more grateful if you considered submitting a publication to one of the journals (which will open for submission in a few weeks) in the near future, in order to help establish their reputation.\n\n" +
                               "I'd be happy to provide you with more information, should you require it. In view of our development plans, I would be grateful if you could react (by replying to this email) within the next two or three weeks, if possible. I'll be looking forward to your reaction, your comments and suggestions, be they positive or negative. If you need more time to consider, that's also fine; just let me know.\n\n")
            elif cls.invitation.invitation_type == 'C':
                email_text += ('The SciPost.org portal has been intensively developed over the last few months. It is legally based on a not-for-profit foundation and will operate in perpetuity as a non-commercial entity at the exclusive service of the academic sector. We are now entering the next phase in the implementation, which is to build up the community of professional academics who will hopefully make use of the portal in their daily activities.\n\n' +
                               "It's perhaps best if you take the time to look at the website itself, which is anchored at scipost.org. Registration is now generally open, but you can also personally register by visiting the following single-use link, containing a partly pre-filled form for your convenience: \n\n" +
                               'https://scipost.org/invitation/' + cls.invitation.invitation_key + '\n\n' +
                               'I will then activate your account. Many details about the initiative can then be found at scipost.org/about and at scipost.org/FAQ.\n\n' +
                               "If you do develop sympathy for the initiative, besides participating in the online platform, we'd be very grateful if you considered submitting a publication to one of the journals (which will open for submission in a few weeks) within the near future, in order to help establish their reputation. I'll also be looking forward to your reaction, your comments and suggestions, be they positive or negative.\n\n")
                
            email_text += ("On behalf of the SciPost Foundation,\n\n" +
                           "Prof. dr Jean-Sébastien Caux\n---------------------------------------------\nInstitute for Theoretial Physics\nUniversity of Amsterdam\nScience Park 904\n1098 XH Amsterdam\nThe Netherlands\n---------------------------------------------\ntel.: +31 (0)20 5255775\nfax: +31 (0)20 5255778\n---------------------------------------------")
                
            emailmessage = EmailMessage(
                'SciPost registration invitation', email_text,
                'J-S Caux <jscaux@scipost.org>',
                [cls.invitation.email],
                ['registration@scipost.org'],
                reply_to=['registration@scipost.org'])

        # This function is now for all invitation types:
        emailmessage.send(fail_silently=False)
    
