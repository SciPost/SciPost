import datetime
import hashlib
import random
import string

from django.contrib.auth.models import User
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template import Context, Template
from django.utils import timezone

from .models import *


SCIPOST_SUMMARY_FOOTER = (
    '\n\n--------------------------------------------------'
    '\n\nAbout SciPost:\n\n'
    'SciPost.org is a publication portal managed by '
    'professional scientists, offering (among others) high-quality '
    'two-way open access journals (free to read, free to publish in) '
    'with an innovative peer-witnessed form of refereeing. '
    'The site also offers a Commentaries section, providing a '
    'means of commenting on all existing literature. SciPost is established as '
    'a not-for-profit foundation devoted to serving the interests of the '
    'international scientific community.'
    '\n\nThe site is anchored at https://scipost.org. Many further details '
    'about SciPost, its principles, ideals and implementation can be found at '
    'https://scipost.org/about and https://scipost.org/FAQ.\n'
    'Professional scientists can register at https://scipost.org/register.'
)

SCIPOST_SUMMARY_FOOTER_HTML = (
    '\n<br/><br/>--------------------------------------------------'
    '<br/><p>About SciPost:</p>'
    '<p>SciPost.org is a publication portal managed by '
    'professional scientists, offering (among others) high-quality '
    'two-way open access journals (free to read, free to publish in) '
    'with an innovative peer-witnessed form of refereeing. '
    'The site also offers a Commentaries section, providing a '
    'means of commenting on all existing literature. SciPost is established as '
    'a not-for-profit foundation devoted to serving the interests of the '
    'international scientific community.</p>'
    '<p>The site is anchored at https://scipost.org. Many further details '
    'about SciPost, its principles, ideals and implementation can be found at '
    'https://scipost.org/about and https://scipost.org/FAQ.\n'
    'Professional scientists can register at https://scipost.org/register.</p>'
)


EMAIL_FOOTER = (
    '\n{% load staticfiles %}'
    '<a href="https://scipost.org"><img src="{% static '
    '\'scipost/images/logo_scipost_with_bgd_small.png\' %}" width="64px"></a><br/>'
    '<div style="background-color: #f0f0f0; color: #002B49; align-items: center;">'
    '<div style="display: inline-block; padding: 8px;">'
    '<a href="https://scipost.org/journals/">Journals</a></div>'
    '<div style="display: inline-block; padding: 8px;">'
    '<a href="https://scipost.org/submissions/">Submissions</a></div>'
    '<div style="display: inline-block; padding: 8px;">'
    '<a href="https://scipost.org/commentaries/">Commentaries</a></div>'
    '<div style="display: inline-block; padding: 8px;">'
    '<a href="https://scipost.org/theses/">Theses</a></div>'
    '<div style="display: inline-block; padding: 8px;">'
    '<a href="https://scipost.org/login/">Login</a></div>'
    '</div>'
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
                      '\n\nYour registration will thereafter be vetted. Many thanks for your interest.'
                      '\n\nThe SciPost Team.')
        email_text_html = (
            'Dear {{ title }} {{ last_name }},<br/>'
            '\n<p>Your request for registration to the SciPost publication portal'
            ' has been received. You now need to validate your email by visiting '
            'this link within the next 48 hours:</p>' 
            '<p><a href="https://scipost.org/activation/{{ activation_key }}">'
            'Activate your account</a></p>'
            '\n<p>Your registration will thereafter be vetted. Many thanks for your interest.</p>'
            '<p>The SciPost Team.</p>')
        email_context = Context({
            'title': title_dict[cls.contributor.title],
            'last_name': cls.contributor.user.last_name,
            'activation_key': cls.contributor.activation_key,
        })
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(email_context)
        #emailmessage = EmailMessage(
        emailmessage = EmailMultiAlternatives(
            'SciPost registration request received', email_text,
            'SciPost registration <registration@scipost.org>', 
            [cls.contributor.user.email],
            ['registration@scipost.org'],
            reply_to=['registration@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
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
            cited_in_publication = cls.form.cleaned_data['cited_in_publication'],
            invited_by = cls.contributor,
            message_style = cls.form.cleaned_data['message_style'],
            personal_message = cls.form.cleaned_data['personal_message'],
            )
        Utils.load({'invitation': invitation})

    @classmethod
    def send_registration_invitation_email(cls, renew=False):
        signature = (title_dict[cls.invitation.invited_by.title] + ' '
                     + cls.invitation.invited_by.user.first_name + ' '
                     + cls.invitation.invited_by.user.last_name)
        if not renew:
            # Generate email activation key and link
            salt = ""
            for i in range(5):
                salt = salt + random.choice(string.ascii_letters)
            salt = salt.encode('utf8')
            invitationsalt = cls.invitation.last_name
            invitationsalt = invitationsalt.encode('utf8')
            cls.invitation.invitation_key = hashlib.sha1(salt+invitationsalt).hexdigest()
        cls.invitation.key_expires = datetime.datetime.strftime(
            datetime.datetime.now() + datetime.timedelta(days=365), "%Y-%m-%d %H:%M:%S")
        if renew:
            cls.invitation.nr_reminders += 1
            cls.invitation.date_last_reminded = timezone.now()
        cls.invitation.save()
        email_text = ''
        email_text_html = ''
        email_context = Context({})
        if renew:
            email_text += ('Reminder: Invitation to SciPost\n'
                           '-------------------------------\n\n')
            email_text_html += ('<strong>Reminder: Invitation to SciPost</strong>'
                               '<br/><hr/><br/>')
        if cls.invitation.invitation_type == 'F':
            email_text += 'RE: Invitation to join the Editorial College of SciPost\n\n'
            email_text_html += ('<strong>RE: Invitation to join the Editorial College '
                                'of SciPost</strong><br/><hr/><br/>')
        email_text += 'Dear '
        email_text_html += 'Dear '
        if cls.invitation.message_style == 'F':
            email_text += title_dict[cls.invitation.title] + ' ' + cls.invitation.last_name
            email_text_html += '{{ title }} {{ last_name }}'
            email_context['title'] = title_dict[cls.invitation.title]
            email_context['last_name'] = cls.invitation.last_name
        else:
            email_text += cls.invitation.first_name
            email_text_html += '{{ first_name }}'
            email_context['first_name'] = cls.invitation.first_name
        email_text +=  ',\n\n'
        email_text_html += ',<br/>'
        if len(cls.invitation.personal_message) > 3:
            email_text += cls.invitation.personal_message + '\n\n'
            email_text_html += '<i>{{ personal_message|linebreaks }}</i><br/>\n'
            email_context['personal_message'] = cls.invitation.personal_message

        # This text to be put in C, ci invitations
        summary_text = (
            '\n\nIn summary, SciPost.org is a publication portal managed by '
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
            '\n\nFor your convenience, a partly pre-filled registration '
            'form has been prepared for you at '
            'https://scipost.org/invitation/' + cls.invitation.invitation_key 
            + ' (you can in any case still register at '
            'https://scipost.org/register).\n\n'
            'If you do develop sympathy for the initiative, besides participating in the '
            'online platform, we would be very grateful if you considered submitting a '
            'publication to one of the journals within the near future, in order to help '
            'establish their reputation. We\'ll also be looking forward to your reaction, '
            'comments and suggestions about the initiative, which we hope you will find '
            'useful to your work as a professional scientist.'
            '\n\nMany thanks in advance for taking a few minutes to look into it,'
            '\n\nOn behalf of the SciPost Foundation,\n\n'
            #'Prof. dr Jean-Sébastien Caux\n---------------------------------------------'
            #'\nInstitute for Theoretical Physics\nUniversity of Amsterdam\nScience Park 904'
            #'\n1098 XH Amsterdam\nThe Netherlands\n'
            #'---------------------------------------------\ntel.: +31 (0)20 5255775'
            #'\nfax: +31 (0)20 5255778\n---------------------------------------------'
            + signature + '\n'
        )

        summary_text_html = (
            '\n<p>In summary, SciPost.org is a publication portal managed by '
            'professional scientists, offering (among others) high-quality '
            'Open Access journals with innovative forms of refereeing, and a '
            'means of commenting on all existing literature. SciPost is established as '
            'a not-for-profit foundation devoted to serving the interests of the '
            'international scientific community.</p>'
            '\n<p>The site is anchored at <a href="https://scipost.org">scipost.org</a>. '
            'Many further details '
            'about SciPost, its principles, ideals and implementation can be found at '
            'the <a href="https://scipost.org/about">about</a> '
            'and <a href="https://scipost.org/FAQ">FAQ</a> pages.</p>'
            '<p>As a professional academic, you can register at the '
            '<a href="https://scipost.org/register">registration page</a>, '
            'enabling you to contribute to the site\'s '
            'contents, for example by offering submissions, reports and comments.</p>'
            '\n<p>For your convenience, a partly pre-filled '
            '<a href="https://scipost.org/invitation/{{ invitation_key }}">registration form</a>'
            ' has been prepared for you (you can in any case still register at the '
            '<a href="https://scipost.org/register">registration page</a>).</p>'
            '\n<p>If you do develop sympathy for the initiative, besides participating in the '
            'online platform, we would be very grateful if you considered submitting a '
            'publication to one of the journals within the near future, in order to help '
            'establish their reputation. We\'ll also be looking forward to your reaction, '
            'comments and suggestions about the initiative, which we hope you will find '
            'useful to your work as a professional scientist.</p>'
            '\n<p>Many thanks in advance for taking a few minutes to look into it,</p>'
            '<p>On behalf of the SciPost Foundation,</p>'
            # '<br/>Prof. dr Jean-Sébastien Caux'
            # '<br/>---------------------------------------------'
            # '<br/>Institute for Theoretical Physics'
            # '<br/>University of Amsterdam'
            # '<br/>Science Park 904'
            # '<br/>1098 XH Amsterdam<br/>The Netherlands'
            # '<br/>---------------------------------------------'
            # '<br/>tel.: +31 (0)20 5255775'
            # '<br/>fax: +31 (0)20 5255778'
            # '<br/>---------------------------------------------'
            '<p>' + signature + '</p>'
        )
        email_context['invitation_key'] = cls.invitation.invitation_key

        if cls.invitation.invitation_type == 'R':
            # Refereeing invitation
            # Details of the submission to referee are already in the personal_message field
            email_text += (
                'We would hereby like to cordially invite you '
                'to become a Contributor on SciPost '
                '(this is required in order to deliver reports; '
                'our records show that you are not yet registered); '
                'for your convenience, we have prepared a pre-filled form for you at\n\n'
                'https://scipost.org/invitation/' + cls.invitation.invitation_key + '\n\n'
                'after which your registration will be activated, allowing you to contribute, '
                'in particular by providing referee reports.\n\n'
                'We very much hope that we can count on your expertise,\n\n'
                'Many thanks in advance,\n\nThe SciPost Team')
            email_text_html += (
                '\n<p>We would hereby like to cordially invite you '
                'to become a Contributor on SciPost '
                '(this is required in order to deliver reports; '
                'our records show that you are not yet registered); '
                'for your convenience, we have prepared a pre-filled '
                '<a href="https://scipost.org/invitation/{{ invitation_key }}">registration form</a> '
                'for you. After activation of your registration, you will be allowed to contribute, '
                'in particular by providing referee reports.</p>'
                '<p>We very much hope that we can count on your expertise,</p>'
                '<p>Many thanks in advance,</p>'
                '<p>The SciPost Team</p>')

            email_text += SCIPOST_SUMMARY_FOOTER
            email_text_html += SCIPOST_SUMMARY_FOOTER_HTML
            email_text_html += '<br/>' + EMAIL_FOOTER
            html_template = Template(email_text_html)
            html_version = html_template.render(email_context)
            #emailmessage = EmailMessage(
            emailmessage = EmailMultiAlternatives(
                'SciPost: refereeing request (and registration invitation)', email_text,
                'SciPost Registration <registration@scipost.org>',
                [cls.invitation.email],
                cc=[cls.invitation.invited_by.user.email],
                bcc=['registration@scipost.org'],
                reply_to=['registration@scipost.org'])
            emailmessage.attach_alternative(html_version, 'text/html')

        elif cls.invitation.invitation_type == 'ci':
            # Has been cited in a Submission. Invite!
            email_text += (
                'Your work has been cited in a manuscript submitted to SciPost,'
                '\n\n' + cls.invitation.cited_in_submission.title 
                + ' by ' + cls.invitation.cited_in_submission.author_list + '.\n\n'
                'I would hereby like to use this opportunity to quickly introduce '
                'you to the SciPost initiative, and to invite you to become an active '
                'Contributor to the site. You might for example consider reporting or '
                'commenting on the above submission before the refereeing deadline.')
            email_text_html += (
                '<p>Your work has been cited in a manuscript submitted to SciPost,</p>'
                '<p>{{ sub_title }} <br>by {{ sub_author_list }},</p>' 
                '<p>which you can find online at the '
                '<a href="https://scipost.org/submission/{{ arxiv_nr_w_vn_nr }}">'
                'submission\'s page</a>.</p>'
                '\n<p>I would hereby like to use this opportunity to quickly introduce '
                'you to the SciPost initiative, and to invite you to become an active '
                'Contributor to the site. You might for example consider reporting or '
                'commenting on the above submission before the refereeing deadline.</p>')
            email_context['sub_title'] = cls.invitation.cited_in_submission.title 
            email_context['sub_author_list'] = cls.invitation.cited_in_submission.author_list
            email_context['arxiv_identifier_w_vn_nr'] = cls.invitation.cited_in_submission.arxiv_identifier_w_vn_nr

            email_text += summary_text
            email_text_html += summary_text_html
            email_text_html += '<br/>' + EMAIL_FOOTER
            html_template = Template(email_text_html)
            html_version = html_template.render(email_context)
            #emailmessage = EmailMessage(
            emailmessage = EmailMultiAlternatives(
                'SciPost: invitation', email_text,
                #'J.-S. Caux <jscaux@scipost.org>',
                'SciPost registration <registration@scipost.org>',
                [cls.invitation.email],
                cc=[cls.invitation.invited_by.user.email],
                bcc=['registration@scipost.org'],
                reply_to=['registration@scipost.org'])
            emailmessage.attach_alternative(html_version, 'text/html')

        elif cls.invitation.invitation_type == 'cp':
            # Has been cited in a Publication. Invite!
            email_text += (
                'Your work has been cited in a paper published by SciPost,'
                '\n\n' + cls.invitation.cited_in_publication.title 
                + '\nby ' + cls.invitation.cited_in_publication.author_list + 
                '\n\n(published as ' + cls.invitation.cited_in_publication.citation()
                + ').\n\n'
                'I would hereby like to use this opportunity to quickly introduce '
                'you to the SciPost initiative, and to invite you to become an active '
                'Contributor to the site.')
            email_text_html += (
                '<p>Your work has been cited in a paper published by SciPost,</p>'
                '<p>{{ pub_title }}</p> <p>by {{ pub_author_list }}<p/>'
                '(published as <a href="https://scipost.org/{{ doi_label }}">{{ citation }}</a>).</p>'
                '\n<p>I would hereby like to use this opportunity to quickly introduce '
                'you to the SciPost initiative, and to invite you to become an active '
                'Contributor to the site. You might for example consider reporting or '
                'commenting on the above submission before the refereeing deadline.</p>')
            email_context['pub_title'] = cls.invitation.cited_in_publication.title 
            email_context['pub_author_list'] = cls.invitation.cited_in_publication.author_list
            email_context['doi_label'] = cls.invitation.cited_in_publication.doi_label
            email_context['citation'] = cls.invitation.cited_in_publication.citation()
            email_text += summary_text
            email_text_html += summary_text_html
            email_text_html += '<br/>' + EMAIL_FOOTER
            html_template = Template(email_text_html)
            html_version = html_template.render(email_context)
            #emailmessage = EmailMessage(
            emailmessage = EmailMultiAlternatives(
                'SciPost: invitation', email_text,
                #'J.-S. Caux <jscaux@scipost.org>',
                'SciPost registration <registration@scipost.org>'
                [cls.invitation.email],
                cc=[cls.invitation.invited_by.user.email],
                bcc=['registration@scipost.org'],
                reply_to=['registration@scipost.org'])
            emailmessage.attach_alternative(html_version, 'text/html')

        elif cls.invitation.invitation_type == 'C':
            email_text += ('I would hereby like to quickly introduce '
                           'you to a scientific publishing initiative '
                           'called SciPost, and to invite you to become an active Contributor.')
            email_text += summary_text
            email_text_html += (
                '<p>I would hereby like to quickly introduce '
                'you to a scientific publishing initiative '
                'called SciPost, and to invite you to become an active Contributor.</p>')
            email_text_html += summary_text_html + '<br/>' + EMAIL_FOOTER
            html_template = Template(email_text_html)
            html_version = html_template.render(email_context)
            #emailmessage = EmailMessage(
            emailmessage = EmailMultiAlternatives(
                'SciPost: invitation', email_text,
                #'J.-S. Caux <jscaux@scipost.org>',
                'SciPost registration <registration@scipost.org>',
                [cls.invitation.email],
                cc=[cls.invitation.invited_by.user.email],
                bcc=['registration@scipost.org'],
                reply_to=['registration@scipost.org'])
            emailmessage.attach_alternative(html_version, 'text/html')

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
            email_text_html += (
                '\n<p>You will have noticed that scientific publishing is currently '
                'undergoing many changes, and you will hopefully agree that it is of '
                'the utmost importance that the best interests of science and scientists '
                'be served by these developments. After much thinking and discussion '
                'about this issue, I recently decided to forge ahead and develop a new '
                'online publication portal by and for scientists, aimed at turning '
                'these ideas into reality.</p>'
                '\n<p>The initiative, called SciPost, aims to build on the best traditions '
                'within our community (as exemplified by the arXiv.org preprint server) by '
                'offering a complete scientific publication platform, run by and for '
                'professional scientists, providing:</p>'
                '\n<ul><li>a means to comment on all existing literature;</li>'
                '<li>a repository of links to theses (Habilitation, PhD, Master\'s);</li>'
                '<li>and, most importantly, a collection of community-run two-way open '
                'access (no subscription fees, no author fees) journals with extremely '
                'stringent (peer-witnessed) refereeing.</li></ul>'
                '\n<p>For the Journals, the main innovations are thus a redesigned, more '
                'accountable refereeing process, together with a new concept for the '
                'editorial process, based on our Editorial College (exclusively composed '
                'of established, professionally practising scientists), designed to '
                'ensure the highest achievable scientific quality while minimizing the '
                'burden of the editorial workflow.</p>'
                '\n<p>SciPost.org is legally based on a not-for-profit foundation and will '
                'operate in perpetuity as a non-commercial entity at the exclusive service '
                'of the academic sector. '
                'The online portal is now operational, and we are currently busy '
                'publicizing it and broadening its user base.</p>'
                '\n<p>To go straight to the point, on behalf of the foundation '
                'and in view of your professional expertise, I hereby would '
                'like to invite you to become an Editorial Fellow and thus join the '
                'Editorial College of SciPost Physics.</p>'
                '\n<p>Please note that only well-known and respected senior academics are '
                'being contacted for this purpose. Academic reputation and involvement '
                'in the community are the most important criteria guiding our '
                'considerations of who should belong to the Editorial College. We '
                'envision each subfield of physics to be represented by around a dozen '
                'Editorial Fellows.</p>'
                '\n<p>To help you in considering this, it would be best if you were to take '
                'the time to look at the website itself, which is anchored at scipost.org. '
                'Registration is now generally open, but you can also personally register '
                '(to become a Contributor, without necessarily committing to membership '
                'of the Editorial College, this to be discussed separately) by visiting '
                'the following <a href="https://scipost.org/invitation/{{ invitation_key }}">'
                'single-use link</a>, containing a partly pre-filled form for '
                'your convenience. I will then activate your account.</p>'
                '\n<p>Many details about the initiative '
                'can then be found at scipost.org/about and at scipost.org/FAQ. '
                'Functioning of the College will proceed according to the by-laws set '
                'out in scipost.org/EdCol_by-laws.</p>'
                '\n<p>Since the success of this initiative is dependent on the involvement of '
                'the very people it is meant to serve, we\'d be very grateful if you were '
                'to give due consideration to this proposal. We would expect you to '
                'commit just 2-4 hours per month to help perform Editorial duties; we will '
                'adjust the number of Editorial Fellows to ensure this is the case. You '
                'could try it out for 6 months or a year, and of course you could quit '
                'any time you wished. We\'d be even more grateful if you considered '
                'submitting a publication to one of the journals, in order to help '
                'establish their reputation.</p>'
                '\n<p>I\'d be happy to provide you with more information, should you require '
                'it. In view of our development plans, I would be grateful if you could '
                'react (by replying to this email) within the next two or three weeks, '
                'if possible. I\'ll be looking forward to your reaction, your comments '
                'and suggestions, be they positive or negative. If you need more time '
                'to consider, that\'s also fine; just let me know.</p>'
                '<p>On behalf of the SciPost Foundation,</p>'
                '<br/>Prof. dr Jean-Sébastien Caux'
                '<br/>---------------------------------------------'
                '<br/>Institute for Theoretial Physics'
                '<br/>University of Amsterdam'
                '<br/>Science Park 904<br/>1098 XH Amsterdam<br/>The Netherlands'
                '<br/>---------------------------------------------'
                '<br/>tel.: +31 (0)20 5255775\nfax: +31 (0)20 5255778'
                '<br/>---------------------------------------------\n')
                
            email_text_html += '<br/>' + EMAIL_FOOTER
            html_template = Template(email_text_html)
            html_version = html_template.render(email_context)
            #emailmessage = EmailMessage(
            emailmessage = EmailMultiAlternatives(
                'SciPost registration invitation', email_text,
                'J-S Caux <jscaux@scipost.org>',
                [cls.invitation.email],
                cc=[cls.invitation.invited_by.user.email],
                bcc=['registration@scipost.org'],
                reply_to=['registration@scipost.org'])
            emailmessage.attach_alternative(html_version, 'text/html')
            

        # This function is now for all invitation types:
        emailmessage.send(fail_silently=False)
    
