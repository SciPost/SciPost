__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template import Context, Template

from .constants import (
    STATUS_VETTED, STATUS_UNCLEAR, STATUS_INCORRECT, STATUS_NOT_USEFUL, STATUS_NOT_ACADEMIC)

from scipost.utils import EMAIL_FOOTER
from common.utils import BaseMailUtil


class SubmissionUtils(BaseMailUtil):
    mail_sender = 'submissions@scipost.org'
    mail_sender_title = 'SciPost Editorial Admin'

    @classmethod
    def send_assignment_request_email(cls):
        """ Requires loading 'assignment' attribute. """
        email_text = ('Dear ' + cls.assignment.to.profile.get_title_display() + ' ' +
                      cls.assignment.to.user.last_name +
                      ', \n\nWe have received a Submission to SciPost ' +
                      'for which we would like you to consider becoming Editor-in-charge:\n\n' +
                      cls.assignment.submission.title + ' by '
                      + cls.assignment.submission.author_list + '.' +
                      '\n\nPlease visit https://scipost.org/submissions/pool ' +
                      'in order to accept or decline (it is important for you to inform us '
                      'even if you decline, since this affects the result '
                      'of the pre-screening process). '
                      'Note that this assignment request is automatically '
                      'deprecated if another Fellow '
                      'takes charge of this Submission or if pre-screening '
                      'fails in the meantime.'
                      '\n\nMany thanks in advance for your collaboration,' +
                      '\n\nThe SciPost Team.')
        email_text_html = (
            '<p>Dear {{ title }} {{ last_name }},</p>'
            '<p>We have received a Submission to SciPost ' +
            'for which we would like you to consider becoming Editor-in-charge:</p>'
            '<p>{{ sub_title }}</p>\n<p>by {{ author_list }}.</p>'
            '\n<p>Please visit the '
            '<a href="https://scipost.org/submissions/pool">Submissions Pool</a> '
            'in order to accept or decline (it is important for you to inform us '
            'even if you decline, since this affects the result '
            'of the pre-screening process).</p>'
            '<p>Note that this assignment request is automatically '
            'deprecated if another Fellow '
            'takes charge of this Submission or if pre-screening '
            'fails in the meantime.</p>'
            '\n<p>Many thanks in advance for your collaboration,</p>'
            '<p>The SciPost Team.</p>')
        email_context = {
            'title': cls.assignment.to.profile.get_title_display(),
            'last_name': cls.assignment.to.user.last_name,
            'sub_title': cls.assignment.submission.title,
            'author_list': cls.assignment.submission.author_list,
        }
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(Context(email_context))
        emailmessage = EmailMultiAlternatives(
            'SciPost: potential Submission assignment', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.assignment.to.user.email],
            bcc=['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)

    @classmethod
    def send_EIC_appointment_email(cls):
        """ Requires loading 'assignment' attribute. """
        r = cls.assignment
        email_text = ('Dear ' + cls.assignment.to.profile.get_title_display() + ' '
                      + cls.assignment.to.user.last_name
                      + ', \n\nThank you for accepting to become Editor-in-charge '
                      'of the SciPost Submission\n\n'
                      + cls.assignment.submission.title + ' by '
                      + cls.assignment.submission.author_list + '.'
                      '\n\nYou can take your editorial actions from the editorial page '
                      'https://scipost.org/submission/editorial_page/'
                      + cls.assignment.submission.preprint.identifier_w_vn_nr
                      + ' (also accessible from your personal page '
                      'https://scipost.org/personal_page under the Editorial Actions tab). '
                      'In particular, unless you choose to directly formulate a Recommendation, '
                      'you should now start a refereeing round and invite at least 3 referees; '
                      'you might want to make sure you are aware of the '
                      'detailed procedure described in the Editorial College by-laws at '
                      'https://scipost.org/EdCol_by-laws.'
                      '\n\nMany thanks in advance for your collaboration,'
                      '\n\nThe SciPost Team.')
        email_text_html = (
            '<p>Dear {{ title }} {{ last_name }},</p>'
            '<p>Thank you for accepting to become Editor-in-charge '
            'of the SciPost Submission</p>'
            '<p>{{ sub_title }}</p>'
            '\n<p>by {{ author_list }}.</p>'
            '\n<p>You can take your editorial actions from the '
            '<a href="https://scipost.org/submission/editorial_page/'
            '{{ identifier_w_vn_nr }}">editorial page</a> '
            '(also accessible from your '
            '<a href="https://scipost.org/personal_page">personal page</a> '
            'under the Editorial Actions tab).</p>'
            '\n<p>In particular, unless you choose to directly formulate a Recommendation, '
            'you should now start a refereeing round and invite at least 3 referees; '
            'you might want to make sure you are aware of the '
            'detailed procedure described in the '
            '<a href="https://scipost.org/EdCol_by-laws">Editorial College by-laws</a>.</p>'
            '<p>Many thanks in advance for your collaboration,</p>'
            '<p>The SciPost Team.</p>')
        email_context = {
            'title': cls.assignment.to.profile.get_title_display(),
            'last_name': cls.assignment.to.user.last_name,
            'sub_title': cls.assignment.submission.title,
            'author_list': cls.assignment.submission.author_list,
            'identifier_w_vn_nr': cls.assignment.submission.preprint.identifier_w_vn_nr,
        }
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(Context(email_context))
        emailmessage = EmailMultiAlternatives(
            'SciPost: assignment as EIC', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.assignment.to.user.email],
            bcc=['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)

    @classmethod
    def send_author_prescreening_passed_email(cls):
        """ Requires loading 'assignment' attribute. """
        email_text = ('Dear ' + cls.assignment.submission.submitted_by.profile.get_title_display() + ' '
                      + cls.assignment.submission.submitted_by.user.last_name
                      + ', \n\nWe are pleased to inform you that your recent Submission to SciPost,\n\n'
                      + cls.assignment.submission.title + ' by ' + cls.assignment.submission.author_list
                      + '\n\nhas successfully passed the pre-screening stage. '
                      '\n\nA Submission Page has been activated at '
                      'https://scipost.org/submission/'
                      + cls.assignment.submission.preprint.identifier_w_vn_nr
                      + ' and a refereeing round has been started, with deadline '
                      'currently set at '
                      + datetime.datetime.strftime(cls.assignment.submission.reporting_deadline, "%Y-%m-%d")
                      + '.\n\n'
                      'During the refereeing round, you are welcome to provide replies to any '
                      'Report or Comment posted on your Submission (you can do so from the '
                      'Submission Page; you will be informed by email of any such Report or '
                      'Comment being delivered). In order to facilitate the work of the '
                      'Editorial College, we recommend limiting these replies to short '
                      'to-the-point clarifications of any issue raised on your manuscript.\n\n'
                      'Please wait for the Editor-in-charge\'s Editorial Recommendation '
                      'before any resubmission of your manuscript.'
                      '\n\nTo facilitate metadata handling, we recommend that all authors '
                      'have an ORCID id (easily obtained from https://orcid.org), '
                      'and be registered as SciPost Contributors. Could we please ask you '
                      '(and your coathors, if any) to ensure that this is the case?'
                      '\n\nWe thank you very much for your contribution.'
                      '\n\nSincerely,' +
                      '\n\nThe SciPost Team.')
        email_text_html = (
            '<p>Dear {{ title }} {{ last_name }},</p>'
            '<p>We are pleased to inform you that your recent Submission to SciPost,</p>'
            '<p>{{ sub_title }}</p>'
            '\n<p>by {{ author_list }}</p>'
            '\n<p>has successfully passed the pre-screening stage.</p>'
            '\n<p>A <a href="https://scipost.org/submission/{{ identifier_w_vn_nr }}">'
            'Submission Page</a> has been activated '
            'and a refereeing round has been started, with deadline '
            'currently set at {{ deadline }}.</p>'
            '<h3>Further procedure</h3>'
            '<p>During the refereeing round, you are welcome to provide replies to any '
            'Report or Comment posted on your Submission (you can do so from the '
            'Submission Page; you will be informed by email of any such Report or '
            'Comment being delivered). In order to facilitate the work of the '
            'Editorial College, we recommend limiting these replies to short '
            'to-the-point clarifications of any issue raised on your manuscript.</p>'
            '<p>Please wait for the Editor-in-charge\'s Editorial Recommendation '
            'before any resubmission of your manuscript.</p>'
            '<h4>Author information</h4>'
            '<p>To facilitate metadata handling, we recommend that all authors '
            'have an ORCID id (easily obtained from <a href="https://orcid.org">orcid.org</a>), '
            'and be registered as SciPost Contributors. Could we please ask you '
            '(and your coathors, if any) to ensure that this is the case?</p>'
            '<p>We thank you very much for your contribution.</p>'
            '<p>Sincerely,</p>'
            '<p>The SciPost Team.</p>')
        email_context = {
            'title': cls.assignment.submission.submitted_by.profile.get_title_display(),
            'last_name': cls.assignment.submission.submitted_by.user.last_name,
            'sub_title': cls.assignment.submission.title,
            'author_list': cls.assignment.submission.author_list,
            'identifier_w_vn_nr': cls.assignment.submission.preprint.identifier_w_vn_nr,
            'deadline': datetime.datetime.strftime(cls.assignment.submission.reporting_deadline,
                                                   "%Y-%m-%d"),
        }
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(Context(email_context))
        emailmessage = EmailMultiAlternatives(
            'SciPost: pre-screening passed', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.assignment.submission.submitted_by.user.email],
            bcc=['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)

    @classmethod
    def send_unreg_ref_reminder_email(cls):
        """
        This method is used to remind a referee who has not yet responded.
        It is used for unregistered referees only.
        It is called from the ref_invitation_reminder method in submissions/views.py.
        """
        email_text = (
            'Dear ' + cls.invitation.get_title_display() + ' '
            + cls.invitation.last_name + ',\n\n'
            'On behalf of the Editor-in-charge '
            + cls.invitation.submission.editor_in_charge.profile.get_title_display() + ' '
            + cls.invitation.submission.editor_in_charge.user.last_name
            + ', we would like to cordially remind you of our recent request to referee\n\n'
            + cls.invitation.submission.title + ' by '
            + cls.invitation.submission.author_list + '.')
        email_text_html = (
            '<p>Dear {{ title }} {{ last_name }},</p>'
            '<p>On behalf of the Editor-in-charge {{ EIC_title }} {{ EIC_last_name }}, '
            'we would like to cordially remind you of our recent request to referee</p>'
            '<p>{{ sub_title }}</p>'
            '\n<p>by {{ author_list }}.</p>')
        email_text += (
            '\n\nWe would also like to renew '
            'our invitation to become a Contributor on SciPost '
            '(our records show that you are not yet registered); '
            'your partially pre-filled registration form is still available at\n\n'
            'https://scipost.org/invitation/' + cls.invitation.invitation_key + '\n\n'
            'after which your registration will be activated, giving you full access to '
            'the portal\'s facilities (in particular allowing you to '
            'provide referee reports).\n\n'
            'To ensure timely processing of the submission (out of respect for the authors), '
            'we would appreciate a quick accept/decline response from you, '
            'ideally within the next 2 days.\n\n'
            'If you are not able to provide a Report, you can quickly let us know by simply '
            'navigating to \n\nhttps://scipost.org/submissions/decline_ref_invitation/'
            + cls.invitation.invitation_key + '\n\n'
            'If you are able to provide a Report, you can confirm this after registering '
            'and logging in (you will automatically be prompted for a confirmation). '
            'Your report can thereafter be submitted by simply clicking on '
            'the "Contribute a Report" link at '
            'https://scipost.org/submission/'
            + cls.invitation.submission.preprint.identifier_w_vn_nr
            + ' before the reporting deadline (currently set at '
            + datetime.datetime.strftime(cls.invitation.submission.reporting_deadline, "%Y-%m-%d")
            + '; your report will be automatically recognized as an invited report). '
            'You might want to make sure you are familiar with our refereeing code of conduct '
            'https://scipost.org/journals/journals_terms_and_conditions and with the '
            'refereeing procedure https://scipost.org/submissions/sub_and_ref_procedure.'
            '\n\nWe very much hope we can count on your expertise,'
            '\n\nMany thanks in advance,\n\nThe SciPost Team'
        )
        email_text_html += (
            '\n<p>We would also like to renew '
            'our invitation to become a Contributor on SciPost '
            '(our records show that you are not yet registered); '
            'your partially pre-filled '
            '<a href="https://scipost.org/invitation/{{ invitation_key }}">'
            'registration form</a> is still available, '
            'after which your registration will be activated, giving you full access to '
            'the portal\'s facilities (in particular allowing you to provide referee reports).</p>'
            '<p>To ensure timely processing of the submission (out of respect for the authors), '
            'we would appreciate a quick accept/decline response from you, '
            'ideally within the next 2 days.</p>'
            '<p>If you are <strong>not</strong> able to provide a Report, '
            'you can quickly let us know by simply '
            '<a href="https://scipost.org/submissions/decline_ref_invitation/{{ invitation_key }}">'
            'clicking here</a>.</p>'
            '<p>If you are able to provide a Report, you can confirm this after registering '
            'and logging in (you will automatically be prompted for a confirmation). '
            'Your report can thereafter be submitted by simply clicking on '
            'the "Contribute a Report" link at '
            'the <a href="https://scipost.org/submission/{{ identifier_w_vn_nr }}">'
            'Submission\'s page</a> before the reporting deadline (currently set at '
            '{{ deadline }}; your report will be automatically recognized as an invited report).</p>'
            '\n<p>You might want to make sure you are familiar with our '
            '<a href="https://scipost.org/journals/journals_terms_and_conditions">'
            'refereeing code of conduct</a> and with the '
            '<a href="https://scipost.org/submissions/sub_and_ref_procedure">'
            'refereeing procedure</a>.</p>'
            '<p>We very much hope we can count on your expertise,</p>'
            '<p>Many thanks in advance,</p>'
            '<p>The SciPost Team</p>')
        email_context = {
            'title': cls.invitation.get_title_display(),
            'last_name': cls.invitation.last_name,
            'EIC_title': cls.invitation.submission.editor_in_charge.profile.get_title_display(),
            'EIC_last_name': cls.invitation.submission.editor_in_charge.user.last_name,
            'sub_title': cls.invitation.submission.title,
            'author_list': cls.invitation.submission.author_list,
            'identifier_w_vn_nr': cls.invitation.submission.preprint.identifier_w_vn_nr,
            'deadline': datetime.datetime.strftime(cls.invitation.submission.reporting_deadline,
                                                   "%Y-%m-%d"),
            'invitation_key': cls.invitation.invitation_key,
        }
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(Context(email_context))
        emailmessage = EmailMultiAlternatives(
            'SciPost: reminder (refereeing request and registration invitation)', email_text,
            'SciPost Refereeing <refereeing@scipost.org>',
            [cls.invitation.email_address],
            bcc=[cls.invitation.submission.editor_in_charge.user.email,
                 'refereeing@scipost.org'],
            reply_to=['refereeing@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)

    @classmethod
    def send_ref_reminder_email(cls):
        """
        This method is used to remind a referee who has not yet responded.
        It is used for registered Contributors only.
        It is called from the ref_invitation_reminder method in submissions/views.py.
        """
        email_text = (
            'Dear ' + cls.invitation.get_title_display() + ' '
            + cls.invitation.last_name + ',\n\n'
            'On behalf of the Editor-in-charge '
            + cls.invitation.submission.editor_in_charge.profile.get_title_display() + ' '
            + cls.invitation.submission.editor_in_charge.user.last_name
            + ', we would like to cordially remind you of our recent request to referee\n\n'
            + cls.invitation.submission.title + ' by '
            + cls.invitation.submission.author_list + '.')
        email_text_html = (
            '<p>Dear {{ title }} {{ last_name }},</p>'
            '<p>On behalf of the Editor-in-charge {{ EIC_title }} {{ EIC_last_name }}, '
            'we would like to cordially remind you of our recent request to referee</p>'
            '<p>{{ sub_title }}</p>'
            '\n<p>by {{ author_list }}.</p>')
        if cls.invitation.accepted is None:
            email_text += (
                '\n\nPlease visit '
                'https://scipost.org/submissions/accept_or_decline_ref_invitations '
                '(login required) as soon as possible (ideally within the next 2 days) '
                'in order to accept or decline this invitation.')
            email_text_html += (
                '\n<p>Please '
                '<a href="https://scipost.org/submissions/accept_or_decline_ref_invitations">'
                'accept or decline the invitation</a> '
                '(login required) as soon as possible (ideally within the next 2 days) '
                'in order to ensure rapid processing of the submission.')
        email_text += (
            '\n\nYour report can be submitted by simply clicking on '
            'the "Contribute a Report" link at '
            'https://scipost.org/submission/'
            + cls.invitation.submission.preprint.identifier_w_vn_nr
            + ' before the reporting deadline (currently set at '
            + datetime.datetime.strftime(cls.invitation.submission.reporting_deadline, "%Y-%m-%d")
            + '; your report will be automatically recognized as an invited report). '
            'You might want to make sure you are familiar with our refereeing code of conduct '
            'https://scipost.org/journals/journals_terms_and_conditions and with the '
            'refereeing procedure https://scipost.org/submissions/sub_and_ref_procedure.'
            '\n\nWe very much hope we can count on your expertise,'
            '\n\nMany thanks in advance,\n\nThe SciPost Team')
        email_text_html += (
            '\n<p>Your report can be submitted by simply clicking on '
            'the "Contribute a Report" link at '
            'the <a href="https://scipost.org/submission/{{ identifier_w_vn_nr }}">'
            'Submission\'s page</a> before the reporting deadline (currently set at '
            '{{ deadline }}; your report will be automatically recognized as an invited report).</p>'
            '\n<p>You might want to make sure you are familiar with our '
            '<a href="https://scipost.org/journals/journals_terms_and_conditions">'
            'refereeing code of conduct</a> and with the '
            '<a href="https://scipost.org/submissions/sub_and_ref_procedure">'
            'refereeing procedure</a>.</p>'
            '<p>We very much hope we can count on your expertise,</p>'
            '<p>Many thanks in advance,</p>'
            '<p>The SciPost Team</p>')
        email_context = {
            'title': cls.invitation.get_title_display(),
            'last_name': cls.invitation.last_name,
            'EIC_title': cls.invitation.submission.editor_in_charge.profile.get_title_display(),
            'EIC_last_name': cls.invitation.submission.editor_in_charge.user.last_name,
            'sub_title': cls.invitation.submission.title,
            'author_list': cls.invitation.submission.author_list,
            'identifier_w_vn_nr': cls.invitation.submission.preprint.identifier_w_vn_nr,
            'deadline': datetime.datetime.strftime(cls.invitation.submission.reporting_deadline,
                                                   "%Y-%m-%d"),
            'invitation_key': cls.invitation.invitation_key,
        }
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(Context(email_context))
        emailmessage = EmailMultiAlternatives(
            'SciPost: reminder (refereeing request and registration invitation)', email_text,
            'SciPost Refereeing <refereeing@scipost.org>',
            [cls.invitation.email_address],
            bcc=[cls.invitation.submission.editor_in_charge.user.email,
                 'refereeing@scipost.org'],
            reply_to=['refereeing@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)

    @classmethod
    def send_ref_cancellation_email(cls):
        """
        This method is used to inform a referee that his/her services are no longer required.
        It is called from the cancel_ref_invitation method in submissions/views.py.
        """
        email_text = ('Dear ' + cls.invitation.get_title_display() + ' '
                      + cls.invitation.last_name + ',\n\n'
                      'On behalf of the Editor-in-charge '
                      + cls.invitation.submission.editor_in_charge.profile.get_title_display() + ' '
                      + cls.invitation.submission.editor_in_charge.user.last_name
                      + ', we would like to inform you that your report on\n\n'
                      + cls.invitation.submission.title + ' by '
                      + cls.invitation.submission.author_list
                      + '\n\nis no longer required.'
                      '\n\nWe very much hope we can count on your expertise '
                      'at some other point in the future,'
                      '\n\nMany thanks for your time,\n\nThe SciPost Team')
        email_text_html = (
            '<p>Dear {{ title }} {{ last_name }},</p>'
            '<p>On behalf of the Editor-in-charge {{ EIC_title }} {{ EIC_last_name }}, '
            'we would like to inform you that your report on</p>'
            '<p>{{ sub_title }}</p>'
            '\n<p>by {{ author_list }}</p>'
            '\n<p>is no longer required.</p>'
            '<p>We very much hope we can count on your expertise '
            'at some other point in the future,</p>'
            '<p>Many thanks for your time,</p>'
            '<p>The SciPost Team</p>')
        if cls.invitation.referee is None:
            email_text += ('\n\nP.S.: We would also like to renew '
                           'our invitation to become a Contributor on SciPost '
                           '(our records show that you are not yet registered); '
                           'your partially pre-filled registration form is still available at\n\n'
                           'https://scipost.org/invitation/' + cls.invitation.invitation_key + '\n\n'
                           'after which your registration will be activated, giving you full access to '
                           'the portal\'s facilities (in particular allowing you to provide referee reports).')
            email_text_html += (
                '\n<br/><p>P.S.: We would also like to renew '
                'our invitation to become a Contributor on SciPost '
                '(our records show that you are not yet registered); '
                'your partially pre-filled '
                '<a href="https://scipost.org/invitation/{{ invitation_key }}">'
                'registration form</a> is still available '
                'after which your registration will be activated, giving you full access to '
                'the portal\'s facilities (in particular allowing you to provide referee reports).</p>')
        email_context = {
            'title': cls.invitation.get_title_display(),
            'last_name': cls.invitation.last_name,
            'EIC_title': cls.invitation.submission.editor_in_charge.profile.get_title_display(),
            'EIC_last_name': cls.invitation.submission.editor_in_charge.user.last_name,
            'sub_title': cls.invitation.submission.title,
            'author_list': cls.invitation.submission.author_list,
            'invitation_key': cls.invitation.invitation_key,
        }
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(Context(email_context))
        emailmessage = EmailMultiAlternatives(
            'SciPost: report no longer needed', email_text,
            'SciPost Refereeing <refereeing@scipost.org>',
            [cls.invitation.email_address],
            bcc=[cls.invitation.submission.editor_in_charge.user.email,
                 'refereeing@scipost.org'],
            reply_to=['refereeing@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)

    @classmethod
    def acknowledge_report_email(cls):
        """ Requires loading 'report' attribute. """
        email_text = ('Dear ' + cls.report.author.profile.get_title_display() + ' ' +
                      cls.report.author.user.last_name + ','
                      '\n\nMany thanks for your Report on Submission\n\n' +
                      cls.report.submission.title + ' by '
                      + cls.report.submission.author_list + '.')
        email_text_html = (
            '<p>Dear {{ ref_title }} {{ ref_last_name }},</p>'
            '<p>Many thanks for your Report on Submission</p>'
            '<p>{{ sub_title }}</p>\n<p>by {{ author_list }}.</p>')
        if cls.report.status == STATUS_VETTED:
            email_text += ('\n\nYour Report has been vetted through and is viewable at '
                           'https://scipost.org/submissions/'
                           + cls.report.submission.preprint.identifier_w_vn_nr + '.')
            email_text_html += (
                '\n<p>Your Report has been vetted through and is viewable at '
                'the <a href="https://scipost.org/submissions/'
                '{{ identifier_w_vn_nr }}">Submission\'s page</a>.</p>')
        else:
            email_text += ('\n\nYour Report has been reviewed by the Editor-in-charge of the Submission, '
                           'who decided not to admit it for online posting, citing the reason: '
                           + cls.report.get_status_display() + '.'
                           ' We copy the text entries of your report below for your convenience, '
                           'if ever you wish to reformulate it and resubmit it.')
            email_text_html += (
                '\n<p>Your Report has been reviewed by the Editor-in-charge of the Submission, '
                'who decided not to admit it for online posting, citing the reason: '
                '{{ refusal_reason }}.</p>'
                '\n<p>We copy the text entries of your report below for your convenience, '
                'if ever you wish to reformulate it and resubmit it.</p>')
        email_text += ('\n\nMany thanks for your collaboration,'
                       '\n\nThe SciPost Team.')
        email_text_html += ('<p>Many thanks for your collaboration,</p>'
                            '<p>The SciPost Team.</p>')
        if cls.report.status != STATUS_VETTED:
            if cls.email_response is not None:
                email_text += '\n\nAdditional info from the Editor-in-charge: \n'
                email_text += cls.email_response
                email_text_html += '\n<p>Additional info from the Editor-in-charge: </p><br/>'
                email_text_html += cls.email_response
            email_text += ('\n\nThe text entries of your Report: ' +
                           '\n\nStrengths: \n' + cls.report.strengths +
                           '\n\nWeaknesses: \n' + cls.report.weaknesses +
                           '\n\nReport: \n' + cls.report.report +
                           '\n\nRequested changes: \n' + cls.report.requested_changes +
                           '\n\nRemarks for Editors: \n' + cls.report.remarks_for_editors)
            email_text_html += (
                '\n<p>The text entries of your Report: </p>'
                '\n<strong>Strengths</strong>: <br/><p>{{ strengths|linebreaks }}</p>'
                '\n<strong>Weaknesses</strong>: <br/><p>{{ weaknesses|linebreaks }}</p>'
                '\n<strong>Report</strong>: <br/><p>{{ report|linebreaks }}</p>'
                '\n<strong>Requested changes</strong>: <br/><p>{{ requested_changes|linebreaks }}</p>'
                '\n<strong>Remarks for Editors</strong>: <br/><p>{{ remarks_for_editors|linebreaks }}</p>')
        email_context = {
            'ref_title': cls.report.author.profile.get_title_display(),
            'ref_last_name': cls.report.author.user.last_name,
            'sub_title': cls.report.submission.title,
            'author_list': cls.report.submission.author_list,
            'identifier_w_vn_nr': cls.report.submission.preprint.identifier_w_vn_nr,
            'strengths': cls.report.strengths,
            'weaknesses': cls.report.weaknesses,
            'report': cls.report.report,
            'requested_changes': cls.report.requested_changes,
            'remarks_for_editors': cls.report.remarks_for_editors,
        }
        if cls.report.status in [STATUS_UNCLEAR, STATUS_INCORRECT,
                                 STATUS_NOT_USEFUL, STATUS_NOT_ACADEMIC]:
            email_context['refusal_reason'] = cls.report.get_status_display()
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(Context(email_context))
        emailmessage = EmailMultiAlternatives(
            'SciPost: Report acknowledgement', email_text,
            'SciPost Refereeing <refereeing@scipost.org>',
            [cls.report.author.user.email],
            bcc=[cls.report.submission.editor_in_charge.user.email,
                 'refereeing@scipost.org'],
            reply_to=['refereeing@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)

    @classmethod
    def send_author_report_received_email(cls):
        """ Requires loading 'report' attribute. """
        email_text = ('Dear ' + cls.report.submission.submitted_by.profile.get_title_display() + ' ' +
                      cls.report.submission.submitted_by.user.last_name +
                      ', \n\nA Report has been posted on your recent Submission to SciPost,\n\n' +
                      cls.report.submission.title + ' by ' + cls.report.submission.author_list + '.'
                      '\n\nYou can view it at the Submission Page '
                      'https://scipost.org/submission/'
                      + cls.report.submission.preprint.identifier_w_vn_nr + '.'
                      '\n\nWe remind you that you can provide an author reply '
                      '(only if you wish, to clarify points raised '
                      'by the report) directly from this Submission Page. '
                      'Any modification to your manuscript '
                      'should await the Recommendation from the Editor-in-charge.'
                      '\n\nWe thank you very much for your contribution.'
                      '\n\nSincerely,' +
                      '\n\nThe SciPost Team.')
        email_text_html = (
            '<p>Dear {{ auth_title }} {{ auth_last_name }},</p>'
            '<p>A Report has been posted on your recent Submission to SciPost,</p>'
            '<p>{{ sub_title }}</p>\n<p>by {{ author_list }}.</p>'
            '\n<p>You can view it at the '
            '<a href="https://scipost.org/submission/{{ identifier_w_vn_nr }}">'
            'Submission\'s page</a>.</p>'
            '<p>We remind you that you can provide an author reply '
            '(only if you wish, to clarify points raised '
            'by the report) directly from this Submission Page. '
            'Any modification to your manuscript '
            'should await the Recommendation from the Editor-in-charge.</p>'
            '\n<p>We thank you very much for your contribution.</p>'
            '<p>Sincerely,</p>'
            '<p>The SciPost Team.</p>')
        email_context = {
            'auth_title': cls.report.submission.submitted_by.profile.get_title_display(),
            'auth_last_name': cls.report.submission.submitted_by.user.last_name,
            'sub_title': cls.report.submission.title,
            'author_list': cls.report.submission.author_list,
            'identifier_w_vn_nr': cls.report.submission.preprint.identifier_w_vn_nr,
        }
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(Context(email_context))
        emailmessage = EmailMultiAlternatives(
            'SciPost: Report received on your Submission', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.report.submission.submitted_by.user.email],
            bcc=['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)


    @classmethod
    def send_communication_email(cls):
        """
        After an EditorialCommunication has been created and saved,
        this method sends emails to the relevant people.
        Requires loading 'communication' attribute.
        """
        recipient_email = []
        bcc_emails = []
        further_action_page = None
        if cls.communication.comtype in ['AtoE', 'RtoE', 'StoE']:
            recipient_email.append(cls.communication.submission.editor_in_charge.user.email)
            recipient_greeting = ('Dear ' +
                                  cls.communication.submission.editor_in_charge.profile.get_title_display() + ' ' +
                                  cls.communication.submission.editor_in_charge.user.last_name)
            further_action_page = ('https://scipost.org/submission/editorial_page/'
                                   + cls.communication.submission.preprint.identifier_w_vn_nr)
            if cls.communication.comtype == 'RtoE':
                bcc_emails.append(cls.communication.referee.user.email)
            bcc_emails.append('submissions@scipost.org')
        elif cls.communication.comtype in ['EtoA']:
            recipient_email.append(cls.communication.submission.submitted_by.user.email)
            recipient_greeting = ('Dear ' +
                                  cls.communication.submission.submitted_by.profile.get_title_display() + ' ' +
                                  cls.communication.submission.submitted_by.user.last_name)
            bcc_emails.append(cls.communication.submission.editor_in_charge.user.email)
            bcc_emails.append('submissions@scipost.org')
        elif cls.communication.comtype in ['EtoR']:
            recipient_email.append(cls.communication.referee.user.email)
            recipient_greeting = ('Dear ' +
                                  cls.communication.referee.profile.get_title_display() + ' ' +
                                  cls.communication.referee.user.last_name)
            bcc_emails.append(cls.communication.submission.editor_in_charge.user.email)
            bcc_emails.append('submissions@scipost.org')
        elif cls.communication.comtype in ['EtoS']:
            recipient_email.append('submissions@scipost.org')
            recipient_greeting = 'Dear Editorial Administrators'
            bcc_emails.append(cls.communication.submission.editor_in_charge.user.email)
            further_action_page = 'https://scipost.org/submissions/pool'

        email_text = (recipient_greeting +
                      ', \n\nPlease find here a communication (' +
                      cls.communication.get_comtype_display() + ') '
                      'concerning Submission\n\n' +
                      cls.communication.submission.title + ' by '
                      + cls.communication.submission.author_list + '.'
                      '\n\nText of the communication:\n------------------------------------------\n' +
                      cls.communication.text + '\n------------------------------------------')
        if further_action_page:
            email_text += '\n\nYou can take follow-up actions from ' + further_action_page + '.'
        email_text += ('\n\nWe thank you very much for your contribution.'
                       '\n\nSincerely,' +
                       '\n\nThe SciPost Team.')
        emailmessage = EmailMessage(
            'SciPost: communication (' + cls.communication.get_comtype_display() + ')',
            email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            recipient_email,
            bcc_emails,
            reply_to=['submissions@scipost.org'])
        emailmessage.send(fail_silently=False)

    @classmethod
    def send_author_revision_requested_email(cls):
        """ Requires loading 'submission' and 'recommendation' attributes. """
        email_text = ('Dear ' + cls.submission.submitted_by.profile.get_title_display() + ' ' +
                      cls.submission.submitted_by.user.last_name +
                      ', \n\nThe Editor-in-charge of your recent Submission to SciPost,\n\n' +
                      cls.submission.title + ' by ' + cls.submission.author_list + ','
                      '\n\nhas formulated an Editorial Recommendation, asking for a ')
        email_text_html = (
            '<p>Dear {{ auth_title }} {{ auth_last_name }},</p>'
            '<p>The Editor-in-charge of your recent Submission to SciPost,</p>'
            '<p>{{ sub_title }}</p>\n<p>by {{ author_list }},</p>'
            '\n<p>has formulated an Editorial Recommendation, asking for a ')
        if cls.recommendation.recommendation == -1:
            email_text += 'minor'
            email_text_html += 'minor'
        elif cls.recommendation.recommendation == -2:
            email_text += 'major'
            email_text_html += 'major'
        email_text += (' revision.'
                       '\n\nYou can view it at the Submission Page '
                       'https://scipost.org/submission/'
                       + cls.submission.preprint.identifier_w_vn_nr + '. '
                       'Note that the recommendation is viewable only by '
                       'the registered authors of the submission.'
                       'To resubmit your paper, please first update the version '
                       'on the arXiv; after appearance, go to the submission page '
                       'https://scipost.org/submissions/submit_manuscript and fill '
                       'in the forms. Your submission will be automatically recognized '
                       'as a resubmission.'
                       '\n\nWe thank you very much for your contribution.'
                       '\n\nSincerely,' +
                       '\n\nThe SciPost Team.')
        email_text_html += (
            ' revision.</p>'
            '\n<p>You can view it at the '
            '<a href="https://scipost.org/submission/'
            '{{ identifier_w_vn_nr }}">Submission\'s Page</a>.</p>'
            '<p>Note that the recommendation is viewable only by '
            'the registered authors of the submission.</p>'
            '<p>To resubmit your paper, please first update the version '
            'on the arXiv; after appearance, go to the '
            '<a href="https://scipost.org/submissions/submit_manuscript">'
            'submission page</a> and fill '
            'the forms in. Your submission will be automatically recognized '
            'as a resubmission.</p>'
            '\n<p>We thank you very much for your contribution.</p>'
            '<p>Sincerely,</p>'
            '<p>The SciPost Team.</p>')
        email_context = {
            'auth_title': cls.submission.submitted_by.profile.get_title_display(),
            'auth_last_name': cls.submission.submitted_by.user.last_name,
            'sub_title': cls.submission.title,
            'author_list': cls.submission.author_list,
            'identifier_w_vn_nr': cls.submission.preprint.identifier_w_vn_nr,
        }
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(Context(email_context))
        emailmessage = EmailMultiAlternatives(
            'SciPost: revision requested', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.submission.submitted_by.user.email],
            bcc=[cls.submission.editor_in_charge.user.email,
                 'submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)

    @classmethod
    def send_author_College_decision_email(cls):
        """ Requires loading 'submission' and 'recommendation' attributes. """
        email_text = ('Dear ' + cls.submission.submitted_by.profile.get_title_display() + ' ' +
                      cls.submission.submitted_by.user.last_name +
                      ', \n\nThe Editorial College of SciPost has taken a decision '
                      'regarding your recent Submission,\n\n' +
                      cls.submission.title + ' by ' + cls.submission.author_list + '.\n\n')
        email_text_html = (
            '<p>Dear {{ auth_title }} {{ auth_last_name }},</p>'
            '<p>The Editorial College of SciPost has taken a decision '
            'regarding your recent Submission,</p>'
            '<p>{{ sub_title }}</p>\n<p>by {{ author_list }}.</p>')
        if (cls.recommendation.recommendation == 1
            or cls.recommendation.recommendation == 2
            or cls.recommendation.recommendation == 3):
            email_text += ('We are pleased to inform you that your Submission '
                           'has been accepted for publication in '
                           + str(cls.recommendation.for_journal)) #submission.submitted_to)
            email_text_html += (
                '<p>We are pleased to inform you that your Submission '
                'has been accepted for publication in <strong>{{ journal }}</strong>')
            if cls.recommendation.recommendation == 1 and False:  # Temporary deactivation of Select
                email_text += (', with a promotion to Select. We warmly congratulate you '
                               'on this achievement, which is reserved to papers deemed in '
                               'the top ten percent of papers we publish.')
                email_text_html += (
                    ', with a promotion to <strong>Select</strong>. We warmly congratulate you '
                    'on this achievement, which is reserved to papers deemed in '
                    'the top ten percent of papers we publish.</p>')
            else:
                email_text += '.'
                email_text_html += '.'
            email_text += ('\n\nYour manuscript will now be taken charge of by our '
                           'production team, who will soon send you proofs '
                           'to check before final publication.')
            email_text_html += ('\n<p>Your manuscript will now be taken charge of by our '
                                'production team, who will soon send you proofs '
                                'to check before final publication.</p>')

        elif cls.recommendation.recommendation == -3:
            email_text += ('We are sorry to inform you that your Submission '
                           'has not been accepted for publication. '
                           '\n\nYou can view more details at the Submission Page '
                           'https://scipost.org/submission/'
                           + cls.submission.preprint.identifier_w_vn_nr + '. '
                           'Note that these details are viewable only by '
                           'the registered authors of the submission.'
                           '\n\nThis Submission Page has now been removed '
                           'from general public view; if you wish, you can email us and '
                           'request to make it publicly visible again.')
            email_text_html += (
                '<p>We are sorry to inform you that your Submission '
                'has not been accepted for publication.</p>'
                '\n<p>You can view more details at the '
                '<a href="https://scipost.org/submission/'
                '{{ identifier_w_vn_nr }}">Submission\'s Page</a>. '
                'Note that these details are viewable only by '
                'the registered authors of the submission.</p>'
                '<p>This Submission Page has now been removed '
                'from general public view; if you wish, you can email us and '
                'request to make it publicly visible again.</p>'
            )
        email_text += ('\n\nWe thank you very much for your contribution.'
                       '\n\nSincerely,'
                       '\n\nThe SciPost Team.')
        email_text_html += ('\n<p>We thank you very much for your contribution.</p>'
                            '<p>Sincerely,</p>'
                            '<p>The SciPost Team.</p>')
        email_context = {
            'auth_title': cls.submission.submitted_by.profile.get_title_display(),
            'auth_last_name': cls.submission.submitted_by.user.last_name,
            'sub_title': cls.submission.title,
            'author_list': cls.submission.author_list,
            'identifier_w_vn_nr': cls.submission.preprint.identifier_w_vn_nr,
            'journal': str(cls.recommendation.for_journal),
        }
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(Context(email_context))
        emailmessage = EmailMultiAlternatives(
            'SciPost: College decision', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.submission.submitted_by.user.email],
            bcc=[cls.submission.editor_in_charge.user.email,
                 'submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)

    @classmethod
    def send_Fellows_voting_reminder_email(cls):
        """
        Requires loading 'Fellow_emails' attribute, which is a list of email addresses.
        """
        email_text = ('Dear Fellow,'
                      '\n\nYou have pending voting duties in the SciPost '
                      'submissions pool at https://scipost.org/submissions/pool'
                      ' (also accessible from your personal page '
                      'https://scipost.org/personal_page under the Editorial Actions tab). '
                      'Could you please have a quick look within the next couple of days, '
                      'so we can finish processing these submissions?'
                      '\n\nMany thanks in advance,'
                      '\n\nThe SciPost Team.')
        email_text_html = (
            '<p>Dear Fellow,</p>'
            '<p>You have pending voting duties in the SciPost '
            'submissions pool https://scipost.org/submissions/pool'
            ' (also accessible from your personal page '
            'https://scipost.org/personal_page under the Editorial Actions tab).</p>'
            '<p>Could you please have a quick look within the next couple of days, '
            'so we can finish processing these submissions?</p>'
            '<p>Many thanks in advance,</p>'
            '<p>The SciPost Team.</p><br/>' + EMAIL_FOOTER)
        email_context = {}
        html_template = Template(email_text_html)
        html_version = html_template.render(Context(email_context))
        emailmessage = EmailMultiAlternatives(
            'SciPost: voting duties', email_text,
            'SciPost Editorial Admin <edadmin@scipost.org>',
            to=['edadmin@scipost.org'],
            bcc=cls.Fellow_emails,
            reply_to=['edadmin@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)
