import datetime

from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template import Context, Template

from journals.models import journals_submit_dict
from scipost.models import title_dict
from scipost.utils import EMAIL_FOOTER

from submissions.models import EditorialAssignment
from submissions.models import assignment_refusal_reasons_dict, ed_comm_choices_dict
from submissions.forms import report_refusal_choices_dict


class SubmissionUtils(object):

    @classmethod
    def load(cls, dict):
        for var_name in dict:
            setattr(cls, var_name, dict[var_name])


    @classmethod
    def deprecate_other_assignments(cls):
        """
        Called when a Fellow has accepted or volunteered to become EIC.
        """
        assignments_to_deprecate = (EditorialAssignment.objects
                                    .filter(submission=cls.assignment.submission, accepted=None)
                                    .exclude(to=cls.assignment.to))
        for atd in assignments_to_deprecate:
            atd.deprecated = True
            atd.save()
            
    @classmethod
    def deprecate_all_assignments(cls):
        """ 
        Called when the pre-screening has failed.
        """
        assignments_to_deprecate = (EditorialAssignment.objects
                                    .filter(submission=cls.assignment.submission, accepted=None))
        for atd in assignments_to_deprecate:
            atd.deprecated = True
            atd.save()


    @classmethod
    def send_authors_submission_ack_email(cls):
        """ Requires loading 'submission' attribute. """
        email_text = ('Dear ' + title_dict[cls.submission.submitted_by.title] + ' ' +
                      cls.submission.submitted_by.user.last_name +
                      ', \n\nWe have received your Submission to SciPost,\n\n' +
                      cls.submission.title + ' by ' + cls.submission.author_list + '.' +
                      '\n\nWe will update you on the results of the pre-screening process '
                      'within the next 5 working days.'
                      '\n\nYou can track your Submission at any time '
                      'from your personal page https://scipost.org/personal_page.' +
                      '\n\nWith many thanks,' +
                      '\n\nThe SciPost Team.')
        email_text_html = (
            'Dear {{ title }} {{ last_name }},<br/>'
            '<p>We have received your Submission to SciPost,</p>'
            '<p>{{ sub_title }}</p>'
            '\n<p>by {{ author_list }}.</p>'
            '\n<p>We will update you on the results of the pre-screening process '
            'within the next 5 working days.</p>'
            '\n<p>You can track your Submission at any time '
            'from your <a href="https://scipost.org/personal_page">personal page</a>.</p>'
            '<p>With many thanks,</p>'
            '<p>The SciPost Team.</p>')
        email_context = Context({
            'title': title_dict[cls.submission.submitted_by.title],
            'last_name': cls.submission.submitted_by.user.last_name,
            'sub_title': cls.submission.title,
            'author_list': cls.submission.author_list,
        })
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(email_context)
        #emailmessage = EmailMessage(
        emailmessage = EmailMultiAlternatives(
            'SciPost: Submission received', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.submission.submitted_by.user.email],
            bcc=['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)
        

    @classmethod
    def send_authors_resubmission_ack_email(cls):
        """ Requires loading 'submission' attribute. """
        email_text = ('Dear ' + title_dict[cls.submission.submitted_by.title] + ' ' +
                      cls.submission.submitted_by.user.last_name +
                      ', \n\nWe have received your Resubmission to SciPost,\n\n' +
                      cls.submission.title + ' by ' + cls.submission.author_list + '.' +
                      '\n\nYou can track your Submission at any time '
                      'from your personal page https://scipost.org/personal_page.' +
                      '\n\nWith many thanks,' +
                      '\n\nThe SciPost Team.')
        email_text_html = (
            'Dear {{ title }} {{ last_name}},<br/>'
            '<p>We have received your Resubmission to SciPost,</p>'
            '<p>{{ sub_title }}</p>'
            '\n<p>by {{ author_list }}.</p>'
            '\n<p>Your manuscript will soon be handled by the Editor-in-charge.</p>'
            '\n<p>You can track your Submission at any time '
            'from your <a href="https://scipost.org/personal_page">personal page</a>.</p>'
            '<p>With many thanks,</p>'
            '<p>The SciPost Team</p>')
        email_context = Context({
            'title': title_dict[cls.submission.submitted_by.title],
            'last_name': cls.submission.submitted_by.user.last_name,
            'sub_title': cls.submission.title,
            'author_list': cls.submission.author_list,
        })
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(email_context)
        #emailmessage = EmailMessage(
        emailmessage = EmailMultiAlternatives(
            'SciPost: Resubmission received', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.submission.submitted_by.user.email],
            bcc=['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)


    @classmethod
    def send_assignment_request_email(cls):
        """ Requires loading 'assignment' attribute. """
        email_text = ('Dear ' + title_dict[cls.assignment.to.title] + ' ' +
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
            'Dear {{ title }} {{ last_name }},'
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
        email_context = Context({
            'title': title_dict[cls.assignment.to.title],
            'last_name': cls.assignment.to.user.last_name,
            'sub_title': cls.assignment.submission.title,
            'author_list': cls.assignment.submission.author_list,
        })
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(email_context)
        #emailmessage = EmailMessage(
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
        email_text = ('Dear ' + title_dict[cls.assignment.to.title] + ' '
                      + cls.assignment.to.user.last_name
                      + ', \n\nThank you for accepting to become Editor-in-charge '
                      'of the SciPost Submission\n\n' 
                      + cls.assignment.submission.title + ' by ' 
                      + cls.assignment.submission.author_list + '.'
                      '\n\nYou can take your editorial actions from the editorial page '
                      'https://scipost.org/submission/editorial_page/' 
                      + cls.assignment.submission.arxiv_identifier_w_vn_nr
                      + ' (also accessible from your personal page '
                      'https://scipost.org/personal_page under the Editorial Actions tab). '
                      'In particular, you should now invite at least 3 referees; you might want to '
                      'make sure you are aware of the '
                      'detailed procedure described in the Editorial College by-laws at '
                      'https://scipost.org/EdCol_by-laws.'
                      '\n\nMany thanks in advance for your collaboration,'
                      '\n\nThe SciPost Team.')
        email_text_html = (
            'Dear {{ title }} {{ last_name }},<br/>'
            '<p>Thank you for accepting to become Editor-in-charge '
            'of the SciPost Submission</p>' 
            '<p>{{ sub_title }}</p>'
            '\n<p>by {{ author_list }}.</p>'
            '\n<p>You can take your editorial actions from the '
            '<a href="https://scipost.org/submission/editorial_page/'
            '{{ arxiv_identifier_w_vn_nr }}">editorial page</a> '
            '(also accessible from your '
            '<a href="https://scipost.org/personal_page">personal page</a> '
            'under the Editorial Actions tab).</p>'
            '\n<p>In particular, you should now invite at least 3 referees; you might want to '
            'make sure you are aware of the '
            'detailed procedure described in the '
            'a href="https://scipost.org/EdCol_by-laws">Editorial College by-laws</a>.</p>'
            '<p>Many thanks in advance for your collaboration,</p>'
            '<p>The SciPost Team.</p>')
        email_context = Context({
            'title': title_dict[cls.assignment.to.title],
            'last_name': cls.assignment.to.user.last_name,
            'sub_title': cls.assignment.submission.title,
            'author_list': cls.assignment.submission.author_list,
            'arxiv_identifier_w_vn_nr': cls.assignment.submission.arxiv_identifier_w_vn_nr,
        })
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(email_context)
        #emailmessage = EmailMessage(
        emailmessage = EmailMultiAlternatives(
            'SciPost: assignment as EIC', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.assignment.to.user.email],
            bcc=['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)


    @classmethod
    def send_EIC_reappointment_email(cls):
        """ Requires loading 'submission' attribute. """
        email_text = ('Dear ' + title_dict[cls.submission.editor_in_charge.title] + ' '
                      + cls.submission.editor_in_charge.user.last_name
                      + ', \n\nThe authors of the SciPost Submission\n\n' 
                      + cls.submission.title + ' by ' 
                      + cls.submission.author_list +
                      '\n\nhave resubmitted their manuscript. '
                      '\n\nAs Editor-in-charge, you can take your editorial actions '
                      'from the editorial page '
                      'https://scipost.org/submission/editorial_page/' 
                      + cls.submission.arxiv_identifier_w_vn_nr
                      + ' (also accessible from your personal page '
                      'https://scipost.org/personal_page under the Editorial Actions tab). '
                      '\n\nYou can either take an immediate acceptance/rejection decision, '
                      'or run a new refereeing round, in which case you '
                      'should now invite at least 3 referees; you might want to '
                      'make sure you are aware of the '
                      'detailed procedure described in the Editorial College by-laws at '
                      'https://scipost.org/EdCol_by-laws.'
                      '\n\nMany thanks in advance for your collaboration,'
                      '\n\nThe SciPost Team.')
        email_text_html = (
            'Dear {{ title }} {{ last_name }},'
            '<p>The authors of the SciPost Submission</p>' 
            '<p>{{ sub_title }}</p>'
            '\n<p>by {{ author_list }}</p>'
            '\n<p>have resubmitted their manuscript.</p>'
            '\n<p>As Editor-in-charge, you can take your editorial actions '
            'from the submission\'s <a href="https://scipost.org/submission/editorial_page/' 
            '{{ arxiv_identifier_w_vn_nr }}">editorial page</a>'
            ' (also accessible from your '
            '<a href="https://scipost.org/personal_page">personal page</a> '
            'under the Editorial Actions tab).</p>'
            '\n<p>You can either take an immediate acceptance/rejection decision, '
            'or run a new refereeing round, in which case you '
            'should now invite at least 3 referees; you might want to '
            'make sure you are aware of the '
            'detailed procedure described in the '
            '<a href="https://scipost.org/EdCol_by-laws">Editorial College by-laws</a>.</p>'
            '<p>Many thanks in advance for your collaboration,</p>'
            '<p>The SciPost Team.</p>')
        email_context = Context({
            'title': title_dict[cls.submission.editor_in_charge.title],
            'last_name': cls.submission.editor_in_charge.user.last_name,
            'sub_title': cls.submission.title,
            'author_list': cls.submission.author_list,
            'arxiv_identifier_w_vn_nr': cls.submission.arxiv_identifier_w_vn_nr,
        })
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(email_context)
        emailmessage = EmailMultiAlternatives(
            'SciPost: resubmission received', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.submission.editor_in_charge.user.email],
            bcc=['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)


    @classmethod
    def send_author_prescreening_passed_email(cls):
        """ Requires loading 'assignment' attribute. """
        email_text = ('Dear ' + title_dict[cls.assignment.submission.submitted_by.title] + ' '
                      + cls.assignment.submission.submitted_by.user.last_name
                      + ', \n\nWe are pleased to inform you that your recent Submission to SciPost,\n\n'
                      + cls.assignment.submission.title + ' by ' + cls.assignment.submission.author_list
                      + '\n\nhas successfully passed the pre-screening stage. '
                      '\n\nA Submission Page has been activated at '
                      'https://scipost.org/submission/' 
                      + cls.assignment.submission.arxiv_identifier_w_vn_nr
                      + ' and a refereeing round has been started, with deadline '
                      'currently set at ' 
                      + datetime.datetime.strftime(cls.assignment.submission.reporting_deadline, "%Y-%m-%d")
                      + '. '
                      '\n\nWe thank you very much for your contribution.'
                      '\n\nSincerely,' +
                      '\n\nThe SciPost Team.')
        email_text_html = (
            'Dear {{ title }} {{ last_name }},'
            '<p>We are pleased to inform you that your recent Submission to SciPost,</p>'
            '<p>{{ sub_title }}</p>'
            '\n<p>by {{ author_list }}</p>'
            '\n<p>has successfully passed the pre-screening stage.</p>'
            '\n<p>A <a href="https://scipost.org/submission/{{ arxiv_identifier_w_vn_nr }}">'
            'Submission Page</a> has been activated '
            'and a refereeing round has been started, with deadline '
            'currently set at {{ deadline }}.</p>' 
            '<p>We thank you very much for your contribution.</p>'
            '<p>Sincerely,</p>'
            '<p>The SciPost Team.</p>')
        email_context = Context({
            'title': title_dict[cls.assignment.submission.submitted_by.title],
            'last_name': cls.assignment.submission.submitted_by.user.last_name,
            'sub_title': cls.assignment.submission.title,
            'author_list': cls.assignment.submission.author_list,
            'arxiv_identifier_w_vn_nr': cls.assignment.submission.arxiv_identifier_w_vn_nr,
            'deadline': datetime.datetime.strftime(cls.assignment.submission.reporting_deadline, 
                                                   "%Y-%m-%d"),
        })
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(email_context)
        #emailmessage = EmailMessage(
        emailmessage = EmailMultiAlternatives(
            'SciPost: pre-screening passed', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.assignment.submission.submitted_by.user.email],
            bcc=['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)

        
    @classmethod
    def assignment_failed_email_authors(cls):
        """ Requires loading 'submission' attribute. """
        email_text = ('Dear ' + title_dict[cls.submission.submitted_by.title] + ' '
                      + cls.submission.submitted_by.user.last_name
                      + ', \n\nYou recent Submission to SciPost,\n\n'
                      + cls.submission.title + ' by ' + cls.submission.author_list
                      + '\n\nhas unfortunately not passed the pre-screening stage. '
                      'We therefore regret to inform you that we will not '
                      'process your paper further towards publication, and that you '
                      'are now free to send your manuscript to an alternative journal.'
                      '\n\nWe nonetheless thank you very much for your contribution.'
                      '\n\nSincerely,' +
                      '\n\nThe SciPost Team.')
        email_text_html = (
            'Dear {{ title }} {{ last_name }},'
            '<p>Your recent Submission to SciPost,</p>'
            '<p>{{ title }}</p>'
            '\n<p>by {{ author_list }}</p>'
            '\n<p>has unfortunately not passed the pre-screening stage. '
            'We therefore regret to inform you that we will not '
            'process your paper further towards publication, and that you '
            'are now free to send your manuscript to an alternative journal.</p>'
            '<p>We nonetheless thank you very much for your contribution.</p>'
            '<p>Sincerely,</p>'
            '<p>The SciPost Team.</p>')
        email_context = Context({
            'title': title_dict[cls.submission.submitted_by.title],
            'last_name': cls.submission.submitted_by.user.last_name,
            'sub_title': cls.submission.title,
            'author_list': cls.submission.author_list,
        })
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(email_context)
        #emailmessage = EmailMessage(
        emailmessage = EmailMultiAlternatives(
            'SciPost: pre-screening not passed', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.submission.submitted_by.user.email],
            bcc=['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)
        

    @classmethod
    def send_refereeing_invitation_email(cls):
        """ 
        This method is called by send_refereeing_invitation in submissions/views.
        It is used when the referee is already a registered contributor.
        If a referee is not yet registered, the method recruit_referee is used 
        instead, which calls the send_registration_email method in scipost/utils.
        Requires loading 'invitation' attribute. 
        """
        email_text = ('Dear ' + title_dict[cls.invitation.referee.title] + ' ' +
                      cls.invitation.referee.user.last_name +
                      ', \n\nWe have received a Submission to SciPost '
                      'which, in view of your expertise and on behalf of the Editor-in-charge '
                      + title_dict[cls.invitation.submission.editor_in_charge.title] + ' ' 
                      + cls.invitation.submission.editor_in_charge.user.last_name
                      + ', we would like to invite you to referee:\n\n'
                      + cls.invitation.submission.title + ' by ' + cls.invitation.submission.author_list
                      + ' (see https://scipost.org/submission/' 
                      + cls.invitation.submission.arxiv_identifier_w_vn_nr + ').'
                      '\n\nPlease visit https://scipost.org/submissions/accept_or_decline_ref_invitations '
                      '(login required) as soon as possible (ideally within the next 2 days) '
                      'in order to accept or decline this invitation.'
                      '\n\nIf you accept, your report can be submitted by simply '
                      'clicking on the "Contribute a Report" link at '
                      'https://scipost.org/submission/' 
                      + cls.invitation.submission.arxiv_identifier_w_vn_nr
                      + ' before the reporting deadline (currently set at ' 
                      + datetime.datetime.strftime(cls.invitation.submission.reporting_deadline, "%Y-%m-%d")
                      + '; your report will be automatically recognized as an invited report). '
                      'You might want to make sure you are familiar with our refereeing code of conduct '
                      'https://scipost.org/journals/journals_terms_and_conditions and with the '
                      'refereeing procedure https://scipost.org/submissions/sub_and_ref_procedure.' 
                      '\n\nWe would be extremely grateful for your contribution, '
                      'and thank you in advance for your consideration.'
                      '\n\nThe SciPost Team.')
        email_text_html = (
            'Dear {{ title }} {{ last_name }},'
            '<p>We have received a Submission to SciPost '
            'which, in view of your expertise and on behalf of the Editor-in-charge '
            '{{ EIC_title }} {{ EIC_last_name }}, '
            'we would like to invite you to referee:</p>'
            '<p>{{ sub_title }}</p>'
            '\n<p>by {{ author_list }}</p>'
            '\n<p>(see <a href="https://scipost.org/submission/' 
            '{{ arxiv_identifier_w_vn_nr }}">this link</a>).</p>'
            '\n<p>Please <a href="https://scipost.org/submissions/accept_or_decline_ref_invitations">'
            'accept or decline the invitation</a> '
            '(login required) as soon as possible (ideally within the next 2 days).</p>'
            '\n<p>If you accept, your report can be submitted by simply '
            'clicking on the "Contribute a Report" link on the '
            '<a href="https://scipost.org/submission/{{ arxiv_identifier_w_vn_nr }}">'
            'Submission\'s Page</a> '
            'before the reporting deadline (currently set at {{ deadline }}' 
            '; your report will be automatically recognized as an invited report).</p>'
            '<p>You might want to make sure you are familiar with our '
            '<a href="https://scipost.org/journals/journals_terms_and_conditions">'
            'refereeing code of conduct</a> and with the '
            '<a href="https://scipost.org/submissions/sub_and_ref_procedure">refereeing procedure</a>.</p>' 
            '\n<p>We would be extremely grateful for your contribution, '
            'and thank you in advance for your consideration.</p>'
            '<p>The SciPost Team.</p>')
        email_context = Context({
            'title': title_dict[cls.invitation.referee.title],
            'last_name': cls.invitation.referee.user.last_name,
            'EIC_title': title_dict[cls.invitation.submission.editor_in_charge.title],
            'EIC_last_name': cls.invitation.submission.editor_in_charge.user.last_name,
            'sub_title': cls.invitation.submission.title,
            'author_list': cls.invitation.submission.author_list,
            'arxiv_identifier_w_vn_nr': cls.invitation.submission.arxiv_identifier_w_vn_nr,
            'deadline': datetime.datetime.strftime(cls.invitation.submission.reporting_deadline, 
                                                   "%Y-%m-%d"),
        })
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(email_context)
        #emailmessage = EmailMessage(
        emailmessage = EmailMultiAlternatives(
            'SciPost: refereeing request', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.invitation.referee.user.email],
            bcc=[cls.invitation.submission.editor_in_charge.user.email,
                 'submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)
    

    @classmethod
    def send_ref_reminder_email(cls):
        """
        This method is used to remind a referee who is not registered as a Contributor.
        It is called from the ref_invitation_reminder method in submissions/views.py.
        """
        email_text = ('Dear ' + title_dict[cls.invitation.title] + ' ' 
                      + cls.invitation.last_name + ',\n\n' 
                      'On behalf of the Editor-in-charge '
                      + title_dict[cls.invitation.submission.editor_in_charge.title] + ' '
                      + cls.invitation.submission.editor_in_charge.user.last_name
                      + ', we would like to cordially remind you of our recent request to referee\n\n'
                      + cls.invitation.submission.title + ' by ' 
                      + cls.invitation.submission.author_list + '.')
        email_text_html = (
            'Dear {{ title }} {{ last_name }},'
            '<p>On behalf of the Editor-in-charge {{ EIC_title }} {{ EIC_last_name }}, '
            'we would like to cordially remind you of our recent request to referee</p>'
            '<p>{{ sub_title }}</p>'
            '\n<p>by {{ author_list }}.</p>')
        if cls.invitation.referee is None:
            email_text += ('\n\nWe would also like to renew '
                           'our invitation to become a Contributor on SciPost '
                           '(our records show that you are not yet registered); '
                           'your partially pre-filled registration form is still available at\n\n'
                           'https://scipost.org/invitation/' + cls.invitation.invitation_key + '\n\n'
                           'after which your registration will be activated, giving you full access to '
                           'the portal\'s facilities (in particular allowing you to provide referee reports).')
            email_text_html += (
                '\n<p>We would also like to renew '
                'our invitation to become a Contributor on SciPost '
                '(our records show that you are not yet registered); '
                'your partially pre-filled '
                '<a href="https://scipost.org/invitation/{{ invitation_key }}">'
                'registration form</a> is still available, '
                'after which your registration will be activated, giving you full access to '
                'the portal\'s facilities (in particular allowing you to provide referee reports).</p>')
        if cls.invitation.accepted is None:
            email_text += ('\n\nPlease visit '
                           'https://scipost.org/submissions/accept_or_decline_ref_invitations '
                           '(login required) as soon as possible (ideally within the next 2 days) '
                           'in order to accept or decline this invitation.')
            email_text_html += (
                '\n<p>Please '
                '<a href="https://scipost.org/submissions/accept_or_decline_ref_invitations">'
                'accept or decline the invitation</a> '
                '(login required) as soon as possible (ideally within the next 2 days) '
                'in order to ensure rapid processing of the submission.')
        email_text += ('\n\nYour report can be submitted by simply clicking on '
                       'the "Contribute a Report" link at '
                       'https://scipost.org/submission/' 
                       + cls.invitation.submission.arxiv_identifier_w_vn_nr 
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
            'the <a href="https://scipost.org/submission/{{ arxiv_identifier_w_vn_nr }}">'
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
        email_context = Context({
            'title': title_dict[cls.invitation.referee.title],
            'last_name': cls.invitation.referee.user.last_name,
            'EIC_title': title_dict[cls.invitation.submission.editor_in_charge.title],
            'EIC_last_name': cls.invitation.submission.editor_in_charge.user.last_name,
            'sub_title': cls.invitation.submission.title,
            'author_list': cls.invitation.submission.author_list,
            'arxiv_identifier_w_vn_nr': cls.invitation.submission.arxiv_identifier_w_vn_nr,
            'deadline': datetime.datetime.strftime(cls.invitation.submission.reporting_deadline, 
                                                   "%Y-%m-%d"),
            'invitation_key': cls.invitation.invitation_key,
        })
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(email_context)
        #emailmessage = EmailMessage(
        emailmessage = EmailMultiAlternatives(
            'SciPost: reminder (refereeing request and registration invitation)', email_text,
            'SciPost Submissions <submissions@scipost.org>',
            [cls.invitation.email_address],
            bcc=[cls.invitation.submission.editor_in_charge.user.email,
                 'submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)


    @classmethod
    def send_ref_cancellation_email(cls):
        """
        This method is used to inform a referee that his/her services are no longer required.
        It is called from the cancel_ref_invitation method in submissions/views.py.
        """
        email_text = ('Dear ' + title_dict[cls.invitation.title] + ' ' 
                      + cls.invitation.last_name + ',\n\n' 
                      'On behalf of the Editor-in-charge '
                      + title_dict[cls.invitation.submission.editor_in_charge.title] + ' '
                      + cls.invitation.submission.editor_in_charge.user.last_name
                      + ', we would like to inform you that your report on\n\n'
                      + cls.invitation.submission.title + ' by ' 
                      + cls.invitation.submission.author_list
                      + '\n\nis no longer required.'
                      '\n\nWe very much hope we can count on your expertise '
                      'at some other point in the future,'
                      '\n\nMany thanks for your time,\n\nThe SciPost Team')
        email_text_html = (
            'Dear {{ title }} {{ last_name }},'
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
        email_context = Context({
            'title': title_dict[cls.invitation.title],
            'last_name': cls.invitation.last_name,
            'EIC_title': title_dict[cls.invitation.submission.editor_in_charge.title],
            'EIC_last_name': cls.invitation.submission.editor_in_charge.user.last_name,
            'sub_title': cls.invitation.submission.title,
            'author_list': cls.invitation.submission.author_list,
            'invitation_key': cls.invitation.invitation_key,
        })
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(email_context)
        #emailmessage = EmailMessage(
        emailmessage = EmailMultiAlternatives(
            'SciPost: report no longer needed', email_text,
            'SciPost Submissions <submissions@scipost.org>',
            [cls.invitation.email_address],
            bcc=[cls.invitation.submission.editor_in_charge.user.email,
                 'submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)
    

    @classmethod
    def email_referee_response_to_EIC(cls):
        """ Requires loading 'invitation' attribute. """
        email_text = ('Dear ' + title_dict[cls.invitation.submission.editor_in_charge.title] + ' ' +
                      cls.invitation.submission.editor_in_charge.user.last_name + ','
                      '\n\nReferee ' + title_dict[cls.invitation.referee.title] + ' ' +
                      cls.invitation.referee.user.last_name + ' has ')
        email_text_html = (
            'Dear {{ EIC_title }} {{ EIC_last_name }},'
            '<p>Referee {{ ref_title }} {{ ref_last_name }} has ')
        email_subject = 'SciPost: referee declines to review'
        if cls.invitation.accepted:
            email_text += 'accepted '
            email_text_html += 'accepted '
            email_subject = 'SciPost: referee accepts to review'
        elif cls.invitation.accepted == False:
            email_text += ('declined (due to reason: ' 
                           + assignment_refusal_reasons_dict[cls.invitation.refusal_reason] + ') ')
            email_text_html += 'declined (due to reason: {{ reason }})' 
            
        email_text += ('to referee Submission\n\n'
                       + cls.invitation.submission.title + ' by ' 
                       + cls.invitation.submission.author_list + '.')
        email_text_html += (
            'to referee Submission</p>'
            '<p>{{ sub_title }}</p>\n<p>by {{ author_list }}.</p>')
        if cls.invitation.accepted == False:
            email_text += ('\n\nPlease invite another referee from the Submission\'s editorial page '
                           'at https://scipost.org/submissions/editorial_page/' 
                           + cls.invitation.submission.arxiv_identifier_w_vn_nr + '.')
            email_text_html += (
                '\n<p>Please invite another referee from the Submission\'s '
                '<a href="https://scipost.org/submissions/editorial_page/'
                '{{ arxiv_identifier_w_vn_nr }}">editorial page</a>.</p>') 
        email_text += ('\n\nMany thanks for your collaboration,'
                       '\n\nThe SciPost Team.')
        email_text_html += ('<p>Many thanks for your collaboration,</p>'
                            '<p>The SciPost Team.</p>')
        email_context = Context({
            'EIC_title': title_dict[cls.invitation.submission.editor_in_charge.title],
            'EIC_last_name': cls.invitation.submission.editor_in_charge.user.last_name,
            'ref_title': title_dict[cls.invitation.referee.title],
            'ref_last_name': cls.invitation.referee.user.last_name,
            'sub_title': cls.invitation.submission.title,
            'author_list': cls.invitation.submission.author_list,
            'arxiv_identifier_w_vn_nr': cls.invitation.submission.arxiv_identifier_w_vn_nr,
        })
        if cls.invitation.refusal_reason:
            email_context['reason'] = assignment_refusal_reasons_dict[cls.invitation.refusal_reason]
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(email_context)
        #emailmessage = EmailMessage(
        emailmessage = EmailMultiAlternatives(
            email_subject, email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.invitation.submission.editor_in_charge.user.email],
            bcc=['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)


    @classmethod
    def email_EIC_report_delivered(cls):
        """ Requires loading 'report' attribute. """
        email_text = ('Dear ' + title_dict[cls.report.submission.editor_in_charge.title] + ' '
                      + cls.report.submission.editor_in_charge.user.last_name + ','
                      '\n\nReferee ' + title_dict[cls.report.author.title] + ' '
                      + cls.report.author.user.last_name +
                      ' has delivered a Report for Submission\n\n'
                      + cls.report.submission.title + ' by ' 
                      + cls.report.submission.author_list + '.'
                      '\n\nPlease vet this Report via your personal page at '
                      'https://scipost.org/personal_page under the Editorial Actions tab.'
                      '\n\nMany thanks for your collaboration,'
                      '\n\nThe SciPost Team.')
        email_text_html = (
            'Dear {{ EIC_title }} {{ EIC_last_name }},'
            '<p>Referee {{ ref_title }} {{ ref_last_name }} '
            'has delivered a Report for Submission</p>'
            '<p>{{ sub_title }}</p>\n<p>by {{ author_list }}.</p>'
            '\n<p>Please vet this Report via your '
            '<a href="https://scipost.org/personal_page">personal page</a> '
            'under the Editorial Actions tab.</p>'
            '<p>Many thanks for your collaboration,</p>'
            '<p>The SciPost Team.</p>')
        email_context = Context({
            'EIC_title': title_dict[cls.report.submission.editor_in_charge.title],
            'EIC_last_name': cls.report.submission.editor_in_charge.user.last_name,
            'ref_title': title_dict[cls.report.author.title],
            'ref_last_name': cls.report.author.user.last_name,
            'sub_title': cls.report.submission.title,
            'author_list': cls.report.submission.author_list,
        })
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(email_context)
        #emailmessage = EmailMessage(
        emailmessage = EmailMultiAlternatives(
            'SciPost: Report delivered', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.report.submission.editor_in_charge.user.email],
            bcc=['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)


    @classmethod
    def acknowledge_report_email(cls):
        """ Requires loading 'report' attribute. """
        email_text = ('Dear ' + title_dict[cls.report.author.title] + ' ' +
                      cls.report.author.user.last_name + ','
                      '\n\nMany thanks for your Report on Submission\n\n' +
                       cls.report.submission.title + ' by ' 
                      + cls.report.submission.author_list + '.')
        email_text_html = (
            'Dear {{ ref_title }} {{ ref_last_name }},'
            '<p>Many thanks for your Report on Submission</p>'
            '<p>{{ sub_title }}</p>\n<p>by{{ author_list }}.</p>')
        if cls.report.status == 1:
            email_text += ('\n\nYour Report has been vetted through and is viewable at '
                           'https://scipost.org/submissions/' 
                           + cls.report.submission.arxiv_identifier_w_vn_nr + '.')
            email_text_html += (
                '\n<p>Your Report has been vetted through and is viewable at '
                'the <a href="https://scipost.org/submissions/' 
                '{{ arxiv_identifier_w_vn_nr }}">Submission\'s page</a>.</p>')
        else:
            email_text += ('\n\nYour Report has been reviewed by the Editor-in-charge of the Submission, '
                           'who decided not to admit it for online posting, citing the reason: '
                           + report_refusal_choices_dict[int(cls.report.status)] + '.'
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
        if cls.report.status != 1:
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
        email_context = Context({
            'ref_title': title_dict[cls.report.author.title],
            'ref_last_name': cls.report.author.user.last_name,
            'sub_title': cls.report.submission.title,
            'author_list': cls.report.submission.author_list,
            'arxiv_identifier_w_vn_nr': cls.report.submission.arxiv_identifier_w_vn_nr,
            'strengths': cls.report.strengths,
            'weaknesses': cls.report.weaknesses,
            'report': cls.report.report,
            'requested_changes': cls.report.requested_changes,
            'remarks_for_editors': cls.report.remarks_for_editors,
        })
        if cls.report.status < 0:
            email_context['refusal_reason'] = report_refusal_choices_dict[int(cls.report.status)]
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(email_context)
        #emailmessage = EmailMessage(
        emailmessage = EmailMultiAlternatives(
            'SciPost: Report acknowledgement', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.report.author.user.email],
            bcc=[cls.report.submission.editor_in_charge.user.email, 
                 'submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)
        

    @classmethod
    def send_author_report_received_email(cls):
        """ Requires loading 'report' attribute. """
        email_text = ('Dear ' + title_dict[cls.report.submission.submitted_by.title] + ' ' +
                      cls.report.submission.submitted_by.user.last_name +
                      ', \n\nA Report has been posted on your recent Submission to SciPost,\n\n' +
                      cls.report.submission.title + ' by ' + cls.report.submission.author_list + '.'
                      '\n\nYou can view it at the Submission Page '
                      'https://scipost.org/submission/' 
                      + cls.report.submission.arxiv_identifier_w_vn_nr + '.'
                      '\n\nWe thank you very much for your contribution.'
                      '\n\nSincerely,' +
                      '\n\nThe SciPost Team.')
        email_text_html = (
            'Dear {{ auth_title }} {{ auth_last_name }},' 
            '<p>A Report has been posted on your recent Submission to SciPost,</p>'
            '<p>{{ sub_title }}</p>\n<p>by {{ author_list }}.</p>'
            '\n<p>You can view it at the '
            '<a href="https://scipost.org/submission/{{ arxiv_identifier_w_vn_nr }}">'
            'Submission\'s page</a>.</p>'
            '\n<p>We thank you very much for your contribution.</p>'
            '<p>Sincerely,</p>'
            '<p>The SciPost Team.</p>')
        email_context = Context({
            'auth_title': title_dict[cls.report.submission.submitted_by.title],
            'auth_last_name': cls.report.submission.submitted_by.user.last_name,
            'sub_title': cls.report.submission.title,
            'author_list': cls.report.submission.author_list,
            'arxiv_identifier_w_vn_nr': cls.report.submission.arxiv_identifier_w_vn_nr,
        })
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(email_context)
        #emailmessage = EmailMessage(
        emailmessage = EmailMultiAlternatives(
            'SciPost: Report received on your Submission', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.report.submission.submitted_by.user.email],
            bcc=['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)

        
    @classmethod
    def send_author_comment_received_email(cls):
        """ Requires loading 'submission' attribute. """
        email_text = ('Dear ' + title_dict[cls.submission.submitted_by.title] + ' ' +
                      cls.submission.submitted_by.user.last_name +
                      ', \n\nA Comment has been posted on your recent Submission to SciPost,\n\n' +
                      cls.submission.title + ' by ' + cls.submission.author_list + '.'
                      '\n\nYou can view it at the Submission Page '
                      'https://scipost.org/submission/' 
                      + cls.submission.arxiv_identifier_w_vn_nr + '.'
                      '\n\nWe thank you very much for your contribution.'
                      '\n\nSincerely,' +
                      '\n\nThe SciPost Team.')
        email_text_html = (
            'Dear {{ auth_title }} {{ auth_last_name }},' 
            '<p>A Comment has been posted on your recent Submission to SciPost,</p>'
            '<p>{{ sub_title }}</p>\n<p>by {{ author_list }}.</p>'
            '\n<p>You can view it at the '
            '<a href="https://scipost.org/submission/{{ arxiv_identifier_w_vn_nr }}">' 
            'Submission\'s Page</a>.</p>'
            '\n<p>We thank you very much for your contribution.</p>'
            '<p>Sincerely,</p>'
            '<p>The SciPost Team.</p>')
        email_context = Context({
            'auth_title': title_dict[cls.submission.submitted_by.title],
            'auth_last_name': cls.submission.submitted_by.user.last_name,
            'sub_title': cls.submission.title,
            'author_list': cls.submission.author_list,
            'arxiv_identifier_w_vn_nr': cls.submission.arxiv_identifier_w_vn_nr,
        })
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(email_context)
        #emailmessage = EmailMessage(
        emailmessage = EmailMultiAlternatives(
            'SciPost: Comment received on your Submission', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.submission.submitted_by.user.email],
            bcc=[cls.submission.editor_in_charge.user.email,
                 'submissions@scipost.org'],
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
                                  title_dict[cls.communication.submission.editor_in_charge.title] + ' ' +
                                  cls.communication.submission.editor_in_charge.user.last_name)
            further_action_page = ('https://scipost.org/submission/editorial_page/' 
                                   + cls.communication.submission.arxiv_identifier_w_vn_nr)
            if cls.communication.comtype == 'AtoE':
                bcc_emails.append(cls.communication.submission.submitted_by.user.email)
            elif cls.communication.comtype == 'RtoE':
                bcc_emails.append(cls.communication.referee.user.email)
            bcc_emails.append('submissions@scipost.org')
        elif cls.communication.comtype in ['EtoA']:
            recipient_email.append(cls.communication.submission.submitted_by.user.email)
            recipient_greeting = ('Dear ' +
                                  title_dict[cls.communication.submission.submitted_by.title] + ' ' +
                                  cls.communication.submission.submitted_by.user.last_name)
            bcc_emails.append(cls.communication.submission.editor_in_charge)
            bcc_emails.append('submissions@scipost.org')
        elif cls.communication.comtype in ['EtoR']:
            recipient_email.append(cls.communication.referee.user.email)
            recipient_greeting = ('Dear ' +
                                  title_dict[cls.communication.referee.title] + ' ' +
                                  cls.communication.referee.user.last_name)
            bcc_emails.append(cls.communication.submission.editor_in_charge)
            bcc_emails.append('submissions@scipost.org')
        elif cls.communication.comtype in ['EtoS']:
            recipient_email.append('submissions@scipost.org')
            recipient_greeting = 'Dear Editorial Administrators'
            bcc_emails.append(cls.communication.submission.editor_in_charge)
            further_action_page = 'https://scipost.org/submissions/pool'
                   
        email_text = (recipient_greeting + 
                      ', \n\nPlease find here a communication (' +
                      ed_comm_choices_dict[cls.communication.comtype] + ') '
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
            'SciPost: communication (' + ed_comm_choices_dict[cls.communication.comtype] + ')',
            email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            recipient_email,
            bcc_emails,
            reply_to=['submissions@scipost.org'])
        emailmessage.send(fail_silently=False)


    @classmethod
    def send_author_revision_requested_email(cls):
        """ Requires loading 'submission' and 'recommendation' attributes. """
        email_text = ('Dear ' + title_dict[cls.submission.submitted_by.title] + ' ' +
                      cls.submission.submitted_by.user.last_name +
                      ', \n\nThe Editor-in-charge of your recent Submission to SciPost,\n\n' +
                      cls.submission.title + ' by ' + cls.submission.author_list + ','
                      '\n\nhas formulated an Editorial Recommendation, asking for a ')
        email_text_html = (
            'Dear {{ auth_title }} {{ auth_last_name }},'
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
                       + cls.submission.arxiv_identifier_w_vn_nr + '. '
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
            '{{ arxiv_identifier_w_vn_nr }}">Submission\'s Page</a>.</p>'
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
        email_context = Context({
            'auth_title': title_dict[cls.submission.submitted_by.title],
            'auth_last_name': cls.submission.submitted_by.user.last_name,
            'sub_title': cls.submission.title,
            'author_list': cls.submission.author_list,
            'arxiv_identifier_w_vn_nr': cls.submission.arxiv_identifier_w_vn_nr,
        })
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(email_context)
        #emailmessage = EmailMessage(
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
        email_text = ('Dear ' + title_dict[cls.submission.submitted_by.title] + ' ' +
                      cls.submission.submitted_by.user.last_name +
                      ', \n\nThe Editorial College of SciPost has taken a decision '
                      'regarding your recent Submission,\n\n' +
                      cls.submission.title + ' by ' + cls.submission.author_list + '.\n\n')
        email_text_html = (
            'Dear {{ auth_title }} {{ auth_last_name }},'
            '<p>The Editorial College of SciPost has taken a decision '
            'regarding your recent Submission,</p>'
            '<p>{{ sub_title }}</p>\n<p>by {{ author_list }}.</p>')
        if (cls.recommendation.recommendation == 1
            or cls.recommendation.recommendation == 2 
            or cls.recommendation.recommendation == 3):
            email_text += ('We are pleased to inform you that your Submission '
                           'has been accepted for publication in ' 
                           + journals_submit_dict[cls.submission.submitted_to_journal])
            email_text_html += (
                '<p>We are pleased to inform you that your Submission '
                'has been accepted for publication in <strong>{{ journal }}</strong>') 
            if cls.recommendation.recommendation == 1:
                email_text += (', with a promotion to Select. We warmly congratulate you '
                               'on this achievement, which is reserved to papers deemed in '
                               'the top ten percent of papers we publish.')
                email_text_html += (
                    ', with a promotion to <strong>Select</strong>. We warmly congratulate you '
                    'on this achievement, which is reserved to papers deemed in '
                    'the top ten percent of papers we publish.</p>')
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
                           + cls.submission.arxiv_identifier_w_vn_nr + '. '
                           'Note that these details are viewable only by '
                           'the registered authors of the submission.')
            email_text_html += (
                '<p>We are sorry to inform you that your Submission '
                'has not been accepted for publication.</p>'
                '\n<p>You can view more details at the '
                '<a href="https://scipost.org/submission/' 
                '{{ arxiv_identifier_w_vn_nr }}">Submission\'s Page</a>. '
                'Note that these details are viewable only by '
                'the registered authors of the submission.</p>'
                '<p>Unless you request otherwise, we will deactivate your '
                'Submission\'s Page and remove it from public view.</p>'
            )
        email_text += ('\n\nWe thank you very much for your contribution.'
                       '\n\nSincerely,'
                       '\n\nThe SciPost Team.')
        email_text += ('\n<p>We thank you very much for your contribution.</p>'
                       '<p>Sincerely,</p>'
                       '<p>The SciPost Team.</p>')
        email_context = Context({
            'auth_title': title_dict[cls.submission.submitted_by.title],
            'auth_last_name': cls.submission.submitted_by.user.last_name,
            'sub_title': cls.submission.title,
            'author_list': cls.submission.author_list,
            'arxiv_identifier_w_vn_nr': cls.submission.arxiv_identifier_w_vn_nr,
            'journal': journals_submit_dict[cls.submission.submitted_to_journal],
        })
        email_text_html += '<br/>' + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(email_context)
        #emailmessage = EmailMessage(
        emailmessage = EmailMultiAlternatives(
            'SciPost: College decision', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.submission.submitted_by.user.email],
            bcc=[cls.submission.editor_in_charge.user.email,
                 'submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.attach_alternative(html_version, 'text/html')
        emailmessage.send(fail_silently=False)
