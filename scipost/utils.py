import datetime
import hashlib
import random
import string

from django.contrib.auth.models import User

from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.template import Context, Template
from django.utils import timezone

from .models import DraftInvitation, RegistrationInvitation

from common.utils import BaseMailUtil


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
    '\n\nDon\'t want to receive such emails? Unsubscribe by '
    'updating your personal data at https://scipost.org/update_personal_data.'
)

EMAIL_UNSUBSCRIBE_LINK_HTML = (
    '\n\n<p style="font-size: 10px;">Don\'t want to receive such emails? Unsubscribe by '
    '<a href="https://scipost.org/update_personal_data">updating your personal data</a>.</p>'
)


class Utils(BaseMailUtil):
    mail_sender = 'registration@scipost.org'
    mail_sender_title = 'SciPost registration'

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
    def email_already_drafted(cls):
        if DraftInvitation.objects.filter(email=cls.form.cleaned_data['email']).exists():
            return True
        else:
            return False

    @classmethod
    def send_registration_email(cls):
        """
        Send mail after registration request has been recieved.

        Requires loading:
        contributor -- Contributor
        """
        cls._send_mail(cls, 'registration_request_received',
                       [cls._context['contributor'].user.email],
                       'request received')

    @classmethod
    def send_new_activation_link_email(cls):
        """
        Send mail after a new activation link on a Contributor has been generated.

        Requires loading:
        contributor -- Contributor
        """
        cls._send_mail(cls, 'new_activation_link',
                       [cls._context['contributor'].user.email],
                       'new email activation link')

    @classmethod
    def create_draft_invitation(cls):
        invitation = DraftInvitation(
            title=cls.form.cleaned_data['title'],
            first_name=cls.form.cleaned_data['first_name'],
            last_name=cls.form.cleaned_data['last_name'],
            email=cls.form.cleaned_data['email'],
            invitation_type=cls.form.cleaned_data['invitation_type'],
            cited_in_submission=cls.form.cleaned_data['cited_in_submission'],
            cited_in_publication=cls.form.cleaned_data['cited_in_publication'],
            drafted_by=cls.contributor,
            )
        invitation.save()

    @classmethod
    def create_invitation(cls):
        invitation = RegistrationInvitation(
            title=cls.form.cleaned_data['title'],
            first_name=cls.form.cleaned_data['first_name'],
            last_name=cls.form.cleaned_data['last_name'],
            email=cls.form.cleaned_data['email'],
            invitation_type=cls.form.cleaned_data['invitation_type'],
            cited_in_submission=cls.form.cleaned_data['cited_in_submission'],
            cited_in_publication=cls.form.cleaned_data['cited_in_publication'],
            invited_by=cls.contributor,
            message_style=cls.form.cleaned_data['message_style'],
            personal_message=cls.form.cleaned_data['personal_message'],
            )
        Utils.load({'invitation': invitation})

    @classmethod
    def send_registration_invitation_email(cls, renew=False):
        signature = (cls.invitation.invited_by.get_title_display() + ' '
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
        email_context = {}
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
            email_text += cls.invitation.get_title_display() + ' ' + cls.invitation.last_name
            email_text_html += '{{ title }} {{ last_name }}'
            email_context['title'] = cls.invitation.get_title_display()
            email_context['last_name'] = cls.invitation.last_name
        else:
            email_text += cls.invitation.first_name
            email_text_html += '{{ first_name }}'
            email_context['first_name'] = cls.invitation.first_name
        email_text += ',\n\n'
        email_text_html += ',<br/>'
        if len(cls.invitation.personal_message) > 3:
            email_text += cls.invitation.personal_message + '\n\n'
            email_text_html += '\n{{ personal_message|linebreaks }}<br/>\n'
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
                'To ensure timely processing of the submission (out of respect for the authors), '
                'we would appreciate a quick accept/decline '
                'response from you, ideally within the next 2 days.\n\n'
                'If you are not able to provide a Report, you can let us know by simply '
                'navigating to \n\nhttps://scipost.org/submissions/decline_ref_invitation/'
                + cls.invitation.invitation_key + '\n\n'
                'If you are able to provide a Report, you can confirm this after registering '
                'and logging in (you will automatically be prompted for a confirmation).\n\n'
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
                '<p>To ensure timely processing of the submission (out of respect for the authors), '
                'we would appreciate a quick accept/decline '
                'response from you, ideally within the next 2 days.</p>'
                '<p>If you are <strong>not</strong> able to provide a Report, '
                'you can let us know by simply '
                '<a href="https://scipost.org/submissions/decline_ref_invitation/{{ invitation_key }}">'
                'clicking here</a>.</p>'
                '<p>If you are able to provide a Report, you can confirm this after registering '
                'and logging in (you will automatically be prompted for a confirmation).</p>'
                '<p>We very much hope that we can count on your expertise,</p>'
                '<p>Many thanks in advance,</p>'
                '<p>The SciPost Team</p>')

            email_text += SCIPOST_SUMMARY_FOOTER
            email_text_html += SCIPOST_SUMMARY_FOOTER_HTML
            email_text_html += '<br/>' + EMAIL_FOOTER
            html_template = Template(email_text_html)
            html_version = html_template.render(Context(email_context))
            emailmessage = EmailMultiAlternatives(
                'SciPost: refereeing request (and registration invitation)', email_text,
                'SciPost Refereeing <refereeing@scipost.org>',
                [cls.invitation.email],
                cc=[cls.invitation.invited_by.user.email],
                bcc=['refereeing@scipost.org'],
                reply_to=['refereeing@scipost.org'])
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
            html_version = html_template.render(Context(email_context))
            emailmessage = EmailMultiAlternatives(
                'SciPost: invitation', email_text,
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
                '<p>{{ pub_title }}</p> <p>by {{ pub_author_list }}</p>'
                '(published as <a href="https://scipost.org/{{ doi_label }}">{{ citation }}</a>).'
                '</p>'
                '\n<p>I would hereby like to use this opportunity to quickly introduce '
                'you to the SciPost initiative, and to invite you to become an active '
                'Contributor to the site.</p>')
            email_context['pub_title'] = cls.invitation.cited_in_publication.title
            email_context['pub_author_list'] = cls.invitation.cited_in_publication.author_list
            email_context['doi_label'] = cls.invitation.cited_in_publication.doi_label
            email_context['citation'] = cls.invitation.cited_in_publication.citation()
            email_text += summary_text
            email_text_html += summary_text_html
            email_text_html += '<br/>' + EMAIL_FOOTER
            html_template = Template(email_text_html)
            html_version = html_template.render(Context(email_context))
            emailmessage = EmailMultiAlternatives(
                'SciPost: invitation', email_text,
                'SciPost registration <registration@scipost.org>',
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
            html_version = html_template.render(Context(email_context))
            emailmessage = EmailMultiAlternatives(
                'SciPost: invitation', email_text,
                'SciPost registration <registration@scipost.org>',
                [cls.invitation.email],
                cc=[cls.invitation.invited_by.user.email],
                bcc=['registration@scipost.org'],
                reply_to=['registration@scipost.org'])
            emailmessage.attach_alternative(html_version, 'text/html')

        elif cls.invitation.invitation_type == 'F':
            email_text += (
                '\nYou will perhaps have already heard about SciPost, a publication '
                'portal established by and for professional scientists.\n'
                '\nSciPost.org is legally based on a not-for-profit foundation and will '
                'operate in perpetuity as a non-commercial entity at the exclusive service '
                'of the academic sector, bringing a cost-slashing alternative to existing '
                'practices.\n'
                '\nSciPost offers a collection of two-way open '
                'access (no subscription fees, no author fees) journals with extremely '
                'stringent (peer-witnessed) refereeing, overseen by '
                'our Editorial College (exclusively composed '
                'of established, professionally practising scientists). The whole process is '
                'designed to ensure the highest achievable scientific quality while making the '
                'editorial workflow as light and efficient as possible.\n'
                '\nTo go straight to the point, on behalf of the foundation '
                'and in view of your professional expertise, I hereby would '
                'like to invite you to become an Editorial Fellow and thus join the '
                'Editorial College of SciPost Physics.\n\n'
                'Please note that only well-known and respected senior academics are '
                'being contacted for this purpose. Academic reputation and involvement '
                'in the community are the most important criteria guiding our '
                'considerations of who should belong to the Editorial College.\n'
                '\nTo help you in considering this, it would be best if you were to take '
                'the time to look at the website itself, which is anchored at scipost.org. '
                'Besides looking around the side, you can also personally register '
                '(to become a Contributor, without necessarily committing to membership '
                'of the Editorial College, this to be discussed separately) by visiting '
                'the following single-use link, containing a partly pre-filled form for '
                'your convenience: \n\n'
                'https://scipost.org/invitation/' + cls.invitation.invitation_key + '.\n'
                '\nMany details about the initiative '
                'can then be found at scipost.org/about and at scipost.org/FAQ. '
                'Functioning of the College will proceed according to the by-laws set '
                'out in scipost.org/EdCol_by-laws.\n\n'
                'Since the success of this initiative is dependent on the involvement of '
                'the very people it is meant to serve, we\'d be very grateful if you were '
                'to give due consideration to this proposal. We would expect you to '
                'commit just 2-4 hours per month to help perform Editorial duties; we will '
                'adjust the number of Editorial Fellows to ensure this is the case. You '
                'could try it out for 6 months or a year, and of course you could quit '
                'any time you wished.\n\n'
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
                '\n<p>You will perhaps have already heard about SciPost, a publication '
                'portal established by and for professional scientists. '
                '\n<p>SciPost.org is legally based on a not-for-profit foundation and will '
                'operate in perpetuity as a non-commercial entity at the exclusive service '
                'of the academic sector, bringing a cost-slashing alternative to existing '
                'practices.</p>'
                '<p>SciPost offers a collection of two-way open '
                'access (no subscription fees, no author fees) journals with extremely '
                'stringent (peer-witnessed) refereeing, overseen by '
                'our Editorial College (exclusively composed '
                'of established, professionally practising scientists). The whole process is '
                'designed to ensure the highest achievable scientific quality while making the '
                'editorial workflow as light and efficient as possible.</p>'
                '\n<p>To go straight to the point, on behalf of the SciPost Foundation '
                'and in view of your professional expertise, I hereby would '
                'like to invite you to become an Editorial Fellow and thus join the '
                'Editorial College of SciPost Physics.</p>'
                '\n<p>Please note that only well-known and respected senior academics are '
                'being contacted for this purpose. Academic reputation and involvement '
                'in the community are the most important criteria guiding our '
                'considerations of who should belong to the Editorial College.</p>'
                '\n<p>To help you in considering this, it would be best if you were to take '
                'the time to look at the website itself, which is anchored at scipost.org. '
                'Besides looking around the site, you can also personally register '
                '(to become a Contributor, without necessarily committing to membership '
                'of the Editorial College, this to be discussed separately) by visiting '
                'the following <a href="https://scipost.org/invitation/{{ invitation_key }}">'
                'single-use link</a>, containing a partly pre-filled form for '
                'your convenience.</p>'
                '\n<p>Many details about the initiative '
                'can then be found at scipost.org/about and at scipost.org/FAQ. '
                'Functioning of the College will proceed according to the by-laws set '
                'out in scipost.org/EdCol_by-laws.</p>'
                '\n<p>Since the success of this initiative is dependent on the involvement of '
                'the very people it is meant to serve, we\'d be very grateful if you were '
                'to give due consideration to this proposal. We would expect you to '
                'commit just 2-4 hours per month to help perform Editorial duties; we will '
                'constantly adjust the number of Editorial Fellows to ensure this is the case. You '
                'could try it out for 6 months or a year, and of course you could quit '
                'any time you wished.</p>'
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
            html_version = html_template.render(Context(email_context))
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

    @classmethod
    def send_citation_notification_email(cls):
        """
        Requires loading the 'notification' attribute.
        """
        email_context = {}
        email_text = ('Dear ' + cls.notification.contributor.get_title_display() +
                      ' ' + cls.notification.contributor.user.last_name)
        email_text_html = 'Dear {{ title }} {{ last_name }}'
        email_context['title'] = cls.notification.contributor.get_title_display()
        email_context['last_name'] = cls.notification.contributor.user.last_name
        email_text += ',\n\n'
        email_text_html += ',<br/>'
        if cls.notification.cited_in_publication:
            url_unsubscribe = reverse('scipost:unsubscribe',
                                      args=[cls.notification.contributor.id,
                                            cls.notification.contributor.activation_key])
            email_text += (
                'We would like to notify you that '
                'your work has been cited in a paper published by SciPost,'
                '\n\n' + cls.notification.cited_in_publication.title
                + '\nby ' + cls.notification.cited_in_publication.author_list +
                '\n\n(published as ' + cls.notification.cited_in_publication.citation() +
                ').\n\nWe hope you will find this paper of interest to your own research.'
                '\n\nBest regards,\n\nThe SciPost Team'
                '\n\nDon\'t want to receive such emails? Unsubscribe by visiting '
                + url_unsubscribe + '.')
            email_text_html += (
                '<p>We would like to notify you that '
                'your work has been cited in a paper published by SciPost,</p>'
                '<p>{{ title }}</p><p>by {{ pub_author_list }}</p>'
                '<p>(published as <a href="https://scipost.org/{{ doi_label }}">'
                '{{ citation }}</a>).</p>'
                '<p>We hope you will find this paper of interest to your own research.</p>'
                '<p>Best regards,</p><p>The SciPost Team</p><br/>'
                + EMAIL_FOOTER + '<br/>'
                '\n<p style="font-size: 10px;">Don\'t want to receive such emails? '
                '<a href="%s">Unsubscribe</a>.</p>' % url_unsubscribe)
            email_context['title'] = cls.notification.cited_in_publication.title
            email_context['pub_author_list'] = cls.notification.cited_in_publication.author_list
            email_context['doi_label'] = cls.notification.cited_in_publication.doi_label
            email_context['citation'] = cls.notification.cited_in_publication.citation()
            email_context['key'] = cls.notification.contributor.activation_key
            html_template = Template(email_text_html)
            html_version = html_template.render(Context(email_context))
        elif cls.notification.cited_in_submission:
            url_unsubscribe = reverse('scipost:unsubscribe',
                                      args=[cls.notification.contributor.id,
                                            cls.notification.contributor.activation_key])
            email_text += (
                'Your work has been cited in a manuscript submitted to SciPost,'
                '\n\n' + cls.notification.cited_in_submission.title
                + ' by ' + cls.notification.cited_in_submission.author_list + '.\n\n'
                'You might for example consider reporting or '
                'commenting on the above submission before the refereeing deadline.\n\n'
                'Best regards,\n\nThe SciPost Team'
                '\n\nDon\'t want to receive such emails? Unsubscribe by visiting '
                + url_unsubscribe + '.')
            email_text_html += (
                '<p>Your work has been cited in a manuscript submitted to SciPost,</p>'
                '<p>{{ sub_title }} <br>by {{ sub_author_list }},</p>'
                '<p>which you can find online at the '
                '<a href="https://scipost.org/submission/{{ arxiv_nr_w_vn_nr }}">'
                'submission\'s page</a>.</p>'
                '<p>You might for example consider reporting or '
                'commenting on the above submission before the refereeing deadline.</p>'
                '<p>Best regards,</p><p>The SciPost Team</p><br/>'
                + EMAIL_FOOTER + '<br/>'
                '\n<p style="font-size: 10px;">Don\'t want to receive such emails? '
                '<a href="%s">Unsubscribe</a>.</p>' % url_unsubscribe)
            email_context['sub_title'] = cls.notification.cited_in_submission.title
            email_context['sub_author_list'] = cls.notification.cited_in_submission.author_list
            email_context['arxiv_identifier_w_vn_nr'] = cls.notification.cited_in_submission.arxiv_identifier_w_vn_nr
            email_context['key'] = cls.notification.contributor.activation_key

        emailmessage = EmailMultiAlternatives(
            'SciPost: citation notification', email_text,
            'SciPost admin <admin@scipost.org>',
            [cls.notification.contributor.user.email],
            bcc=['admin@scipost.org'],
            reply_to=['admin@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)
