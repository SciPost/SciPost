import datetime
import hashlib
import random
import string

from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.utils import timezone

from .models import *


EMAIL_FOOTER = (
    '{% load staticfiles %}'
    # '<ul style="background-color: #f0f0f0; color: #002B49; list-style-type: none; padding: 5px 5px;">'
    # '<li style="display: inline; margin: 0px; padding: 0px;">'
    # '<a href="https://scipost.org">'
    # '<img src="{% static \'scipost/images/logo_scipost_with_bgd_small.png\' %}" width="64px" '
    # 'style="margin: 0px; padding: 0px;"></a></li>'
    # '<li style="display: inline; margin: 3px; padding: 3px;">'
    # '<a href="https://scipost.org/journals/" style="padding: 3px;">Journals</a></li>'
    # '<li style="display: inline; margin: 3px; padding: 3px;">'
    # '<a href="https://scipost.org/submissions/" style="padding: 3px;">Submissions</a></li>'
    # '<li style="display: inline; margin: 3px; padding: 3px;">'
    # '<a href="https://scipost.org/commentaries/" style="padding: 3px;">Commentaries</a></li>'
    # '<li style="display: inline; margin: 3px; padding: 3px;">'
    # '<a href="https://scipost.org/theses/" style="padding: 3px;">Theses</a></li>'
    # '<li style="display: inline; margin: 3px; padding: 3px;">'
    # '<a href="https://scipost.org/login/" style="padding: 3px;">Login</a></li>'
    # '</ul>'
    '<ul style="background-color: #f0f0f0; color: #002B49; list-style-type: none; '
    'display: flex; align-items: center;">'
    '<li style="display: inline-block;">'
    '<a href="https://scipost.org">'
    '<img src="{% static \'scipost/images/logo_scipost_with_bgd_small.png\' %}" width="64px"></a></li>'
    '<li style="display: inline-block; padding 3px;">'
    '<a href="https://scipost.org/journals/">Journals</a></li>'
    '<li style="display: inline-block; padding 3px;">'
    '<a href="https://scipost.org/submissions/">Submissions</a></li>'
    '<li style="display: inline-block; padding 3px;">'
    '<a href="https://scipost.org/commentaries/">Commentaries</a></li>'
    '<li style="display: inline-block; padding 3px;">'
    '<a href="https://scipost.org/theses/">Theses</a></li>'
    '<li style="display: inline-block; padding 3px;">'
    '<a href="https://scipost.org/login/">Login</a></li>'
    '</ul>'
)

EMAIL_UNSUBSCRIBE_LINK_PLAIN = (
    '\n\nUnsubscribe from our email list by '
    'updating your personal data at https://scipost.org/update_personal_data.'
)

EMAIL_UNSUBSCRIBE_LINK = (
    '\n\n<p style="font-size: 10px;">Unsubscribe from our email list by '
    '<a href="https://scipost.org/update_personal_data">updating your personal data</a>.</p>'
)

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
            cited_in_submission = cls.form.cleaned_data['cited_in_submission'],
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

        # This text to be put in C, ci invitations
        summary_text = ('\n\nIn summary, SciPost.org is a publication portal managed by '
                        'professional scientists, offering (among others) high-quality '
                        'Open Access journals with innovative forms of refereeing, and a '
                        'means of commenting on all existing literature. SciPost is established as '
                        'a not-for-profit foundation devoted to serving the interests of the '
                        'international scientific community.'
                        '\n\nThe site is anchored at https://scipost.org. Many further details '
                        'about SciPost, its principles, ideals and implementation can be found at '
                        'https://scipost.org/about and https://scipost.org/FAQ.'
                        '\n\nAs a professional academic, you can register at '
                        'https://scipost.org/register, enabling you to contribute to the site\'s '
                        'contents, for example by offering submissions, reports and comments.'
                        '\n\nFor your convenience, I have prepared a partly pre-filled registration '
                        'form at https://scipost.org/invitation/' + cls.invitation.invitation_key 
                        + ' (valid for two weeks; you can thereafter still register at '
                        'https://scipost.org/register).\n\n'
                        'If you do develop sympathy for the initiative, besides participating in the '
                        'online platform, I would be very grateful if you considered submitting a '
                        'publication to one of the journals within the near future, in order to help '
                        'establish their reputation. I\'ll also be looking forward to your reaction, '
                        'comments and suggestions about the initiative, which I hope you will find '
                        'useful to your work as a professional scientist.'
                        '\n\nMany thanks in advance for taking a few minutes to look into it,'
                        '\n\nOn behalf of the SciPost Foundation,\n\n'
                        'Prof. dr Jean-Sébastien Caux\n---------------------------------------------'
                        '\nInstitute for Theoretical Physics\nUniversity of Amsterdam\nScience Park 904'
                        '\n1098 XH Amsterdam\nThe Netherlands\n'
                        '---------------------------------------------\ntel.: +31 (0)20 5255775'
                        '\nfax: +31 (0)20 5255778\n---------------------------------------------')


        if cls.invitation.invitation_type == 'R':
            # Refereeing invitation
            # Details of the submission to referee are already in the personal_message field
            email_text += ('We would hereby like to cordially invite you '
                           'to become a Contributor on SciPost '
                           '(this is required in order to deliver reports; '
                           'our records show that you are not yet registered); '
                           'for your convenience, we have prepared a pre-filled form for you at\n\n'
                           'https://scipost.org/invitation/' + cls.invitation.invitation_key + '\n\n'
                           'after which your registration will be activated, allowing you to contribute, '
                           'in particular by providing referee reports.\n\n'
                           'We very much hope that we can count on your expertise,\n\n'
                           'Many thanks in advance,\n\nThe SciPost Team')
            email_text += ('\n\n--------------------------------------------------'
                           '\n\nAbout SciPost:\n\n'
                           'In summary, SciPost.org is a publication portal managed by '
                           'professional scientists, offering (among others) high-quality '
                           'Open Access journals with innovative forms of refereeing, and a '
                           'means of commenting on all existing literature. SciPost is established as '
                           'a not-for-profit foundation devoted to serving the interests of the '
                           'international scientific community.'
                           '\n\nThe site is anchored at https://scipost.org. Many further details '
                           'about SciPost, its principles, ideals and implementation can be found at '
                           'https://scipost.org/about and https://scipost.org/FAQ.')

            emailmessage = EmailMessage(
                'SciPost: refereeing request (and registration invitation)', email_text,
                'SciPost Registration <registration@scipost.org>',
                [cls.invitation.email],
                ['registration@scipost.org'],
                reply_to=['registration@scipost.org'])

        elif cls.invitation.invitation_type == 'ci':
            # Has been cited in a Submission. Invite!
            email_text += ('Your work has been cited in a manuscript submitted to SciPost,'
                           '\n\n' + cls.invitation.cited_in_submission.title 
                           + ' by ' + cls.invitation.cited_in_submission.author_list + '.\n\n'
                           'I would hereby like to use this opportunity to quickly introduce '
                           'you to the SciPost initiative, and to invite you to become an active '
                           'Contributor to the site. You might for example consider reporting or '
                           'commenting on the above submission before the refereeing deadline.')
            email_text += summary_text
            emailmessage = EmailMessage(
                'SciPost: invitation', email_text,
                'J.-S. Caux <jscaux@scipost.org>',
                [cls.invitation.email],
                ['registration@scipost.org'],
                reply_to=['registration@scipost.org'])

        elif cls.invitation.invitation_type == 'C':
            email_text += ('I would hereby like to quickly introduce '
                           'you to a scientific publishing initiative I recently launched, '
                           'called SciPost, and to invite you to become an active Contributor.')
            email_text += summary_text
            emailmessage = EmailMessage(
                'SciPost: invitation', email_text,
                'J.-S. Caux <jscaux@scipost.org>',
                [cls.invitation.email],
                ['registration@scipost.org'],
                reply_to=['registration@scipost.org'])

        elif cls.invitation.invitation_type == 'F':
            email_text += ('You will have noticed that scientific publishing is currently '
                           'undergoing many changes, and you will hopefully agree that it is of '
                           'the utmost importance that the best interests of science and scientists '
                           'be served by these developments. After much thinking and discussion '
                           'about this issue, I recently decided to forge ahead and develop a new '
                           'online publication portal by and for scientists, aimed at turning '
                           'these ideas into reality.'
                           '\n\nThe initiative, called SciPost, aims to build on the best traditions '
                           'within our community (as exemplified by the arXiv.org preprint server) by '
                           'offering a complete scientific publication platform, run by and for '
                           'professional scientists, providing:\n\n'
                           '- a means to comment on all existing literature;\n\n'
                           '- a repository of links to theses (Habilitation, PhD, Master\'s);\n\n'
                           '- and, most importantly, a collection of community-run two-way open '
                           'access (no subscription fees, no author fees) journals with extremely '
                           'stringent (peer-witnessed) refereeing.\n\n'
                           'For the Journals, the main innovations are thus a redesigned, more '
                           'accountable refereeing process, together with a new concept for the '
                           'editorial process, based on our Editorial College (exclusively composed '
                           'of established, professionally practising scientists), designed to '
                           'ensure the highest achievable scientific quality while minimizing the '
                           'burden of the editorial workflow.\n\n'
#                           'The SciPost.org portal has been intensively developed over the last '
#                           'few months. It is legally based on a not-for-profit foundation and will '
#                           'operate in perpetuity as a non-commercial entity at the exclusive service '
#                           'of the academic sector. We are now entering the next phase in the '
#                           'implementation, which is to build up the community of professional '
#                           'academics who will help operate it.\n\n'
                           'SciPost.org is legally based on a not-for-profit foundation and will '
                           'operate in perpetuity as a non-commercial entity at the exclusive service '
                           'of the academic sector. '
                           'The online portal is now operational, and we are currently busy '
                           'publicizing it and broadening its user base. \n\n'
                           'To go straight to the point, on behalf of the foundation '
                           'and in view of your professional expertise, I hereby would '
                           'like to invite you to become an Editorial Fellow and thus join the '
                           'Editorial College of SciPost Physics.\n\n'
                           'Please note that only well-known and respected senior academics are '
                           'being contacted for this purpose. Academic reputation and involvement '
                           'in the community are the most important criteria guiding our '
                           'considerations of who should belong to the Editorial College. We '
                           'envision each subfield of physics to be represented by around a dozen '
                           'Editorial Fellows.\n\n'
                           'To help you in considering this, it would be best if you were to take '
                           'the time to look at the website itself, which is anchored at scipost.org. '
                           'Registration is now generally open, but you can also personally register '
                           '(to become a Contributor, without necessarily committing to membership '
                           'of the Editorial College, this to be discussed separately) by visiting '
                           'the following single-use link, containing a partly pre-filled form for '
                           'your convenience: \n\n'
                           'https://scipost.org/invitation/' + cls.invitation.invitation_key + '\n\n'
                           'I will then activate your account. Many details about the initiative '
                           'can then be found at scipost.org/about and at scipost.org/FAQ. '
                           'Functioning of the College will proceed according to the by-laws set '
                           'out in scipost.org/EdCol_by-laws.\n\n'
                           'Since the success of this initiative is dependent on the involvement of '
                           'the very people it is meant to serve, we\'d be very grateful if you were '
                           'to give due consideration to this proposal. We would expect you to '
                           'commit just 2-4 hours per month to help perform Editorial duties; we will '
                           'adjust the number of Editorial Fellows to ensure this is the case. You '
                           'could try it out for 6 months or a year, and of course you could quit '
                           'any time you wished. We\'d be even more grateful if you considered '
                           'submitting a publication to one of the journals, in order to help '
                           'establish their reputation.\n\n'
                           'I\'d be happy to provide you with more information, should you require '
                           'it. In view of our development plans, I would be grateful if you could '
                           'react (by replying to this email) within the next two or three weeks, '
                           'if possible. I\'ll be looking forward to your reaction, your comments '
                           'and suggestions, be they positive or negative. If you need more time '
                           'to consider, that\'s also fine; just let me know.\n\n'
                           'On behalf of the SciPost Foundation,\n\n'
                           'Prof. dr Jean-Sébastien Caux\n---------------------------------------------'
                           '\nInstitute for Theoretial Physics\nUniversity of Amsterdam'
                           '\nScience Park 904\n1098 XH Amsterdam\nThe Netherlands'
                           '\n---------------------------------------------\n'
                           'tel.: +31 (0)20 5255775\nfax: +31 (0)20 5255778'
                           '\n---------------------------------------------')
                
            emailmessage = EmailMessage(
                'SciPost registration invitation', email_text,
                'J-S Caux <jscaux@scipost.org>',
                [cls.invitation.email],
                ['registration@scipost.org'],
                reply_to=['registration@scipost.org'])

        # This function is now for all invitation types:
        emailmessage.send(fail_silently=False)
    
