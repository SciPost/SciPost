import datetime

from django.core.mail import EmailMessage

from scipost.models import title_dict

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
                      + str(cls.assignment.submission.id)
                      + ' (also accessible from your personal page '
                      'https://scipost.org/personal_page under the Editorial Actions tab). '
                      'In particular, you should now invite at least 3 referees; you might want to '
                      'make sure you are aware of the '
                      'detailed procedure described in the Editorial College by-laws at '
                      'https://scipost.org/EdCol_by-laws.'
                      '\n\nMany thanks in advance for your collaboration,'
                      '\n\nThe SciPost Team.')
        emailmessage = EmailMessage(
            'SciPost: assignment as EIC', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.assignment.to.user.email],
            ['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
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
                      'https://scipost.org/submission/' + str(cls.assignment.submission.id)
                      + ' and a refereeing round has been started, with deadline '
                      'currently set at ' 
                      + datetime.datetime.strftime(cls.assignment.submission.reporting_deadline, "%Y-%m-%d")
                      + '. '
                      '\n\nWe thank you very much for your contribution.'
                      '\n\nSincerely,' +
                      '\n\nThe SciPost Team.')
        emailmessage = EmailMessage(
            'SciPost: pre-screening passed', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.assignment.submission.submitted_by.user.email],
            ['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
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
        emailmessage = EmailMessage(
            'SciPost: pre-screening not passed', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.submission.submitted_by.user.email],
            ['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
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
                      + ' (see https://scipost.org/submission/' + str(cls.invitation.submission.id) + ').'
                      '\n\nPlease visit https://scipost.org/submissions/accept_or_decline_ref_invitations '
                      '(login required) as soon as possible (ideally within the next 2 days) '
                      'in order to accept or decline this invitation.'
                      '\n\nIf you accept, your report can be submitted by simply '
                      'clicking on the "Contribute a Report" link at '
                      'https://scipost.org/submission/' + str(cls.invitation.submission.id) 
                      + ' before the reporting deadline (currently set at ' 
                      + datetime.datetime.strftime(cls.invitation.submission.reporting_deadline, "%Y-%m-%d")
                      + '; your report will be automatically recognized as an invited report). '
                      'You might want to make sure you are familiar with our refereeing code of conduct '
                      'https://scipost.org/journals/journals_terms_and_conditions and with the '
                      'refereeing procedure https://scipost.org/submissions/sub_and_ref_procedure.' 
                      '\n\nWe would be extremely grateful for your contribution, '
                      'and thank you in advance for your consideration.'
                      '\n\nThe SciPost Team.')
        emailmessage = EmailMessage(
            'SciPost: refereeing request', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.invitation.referee.user.email],
            ['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.send(fail_silently=False)
    

    @classmethod
    def send_ref_reminder_email(cls):
        """
        This method is used to remind a referee who is not registered as a Contributor.
        It is called from the ref_invitation_reminder method in submissions/views.py.
        """
        email_text = ('Dear ' + title_dict[cls.invitation.title] + ' ' + cls.invitation.last_name + ',\n\n' 
                      'On behalf of the Editor-in-charge '
                      + title_dict[cls.invitation.submission.editor_in_charge.title] + ' '
                      + cls.invitation.submission.editor_in_charge.user.last_name
                      + ', we would like to cordially remind you of our recent request to referee\n\n'
                      + cls.invitation.submission.title + ' by ' 
                      + cls.invitation.submission.author_list + '.')
        if cls.invitation.referee is None:
            email_text += ('\n\nWe would also like to renew '
                           'our invitation to become a Contributor on SciPost '
                           '(our records show that you are not yet registered); '
                           'your partially pre-filled registration form is still available at\n\n'
                           'https://scipost.org/invitation/' + cls.invitation.invitation_key + '\n\n'
                           'after which your registration will be activated, giving you full access to '
                           'the portal\'s facilities (in particular allowing you to provide referee reports).')
        if cls.invitation.accepted is None:
            email_text += ('\n\nPlease visit '
                           'https://scipost.org/submissions/accept_or_decline_ref_invitations '
                           '(login required) as soon as possible (ideally within the next 2 days) '
                           'in order to accept or decline this invitation.')
        email_text += ('\n\nYour report can be submitted by simply clicking on '
                       'the "Contribute a Report" link at '
                       'https://scipost.org/submission/' + str(cls.invitation.submission.id) 
                       + ' before the reporting deadline (currently set at ' 
                       + datetime.datetime.strftime(cls.invitation.submission.reporting_deadline, "%Y-%m-%d")
                       + '; your report will be automatically recognized as an invited report). '
                       'You might want to make sure you are familiar with our refereeing code of conduct '
                       'https://scipost.org/journals/journals_terms_and_conditions and with the '
                       'refereeing procedure https://scipost.org/submissions/sub_and_ref_procedure.')
        email_text += ('\n\nWe very much hope we can count on your expertise,'
                       '\n\nMany thanks in advance,\n\nThe SciPost Team')
        emailmessage = EmailMessage(
            'SciPost: reminder (refereeing request and registration invitation)', email_text,
            'SciPost Submissions <submissions@scipost.org>',
            [cls.invitation.email_address],
            ['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.send(fail_silently=False)
    

    @classmethod
    def email_referee_response_to_EIC(cls):
        """ Requires loading 'invitation' attribute. """
        email_text = ('Dear ' + title_dict[cls.invitation.submission.editor_in_charge.title] + ' ' +
                      cls.invitation.submission.editor_in_charge.user.last_name + ','
                      '\n\nReferee ' + title_dict[cls.invitation.referee.title] + ' ' +
                      cls.invitation.referee.user.last_name + ' has ')
        email_subject = 'SciPost: referee declines to review'
        if cls.invitation.accepted:
            email_text += 'accepted '
            email_subject = 'SciPost: referee accepts to review'
        elif cls.invitation.accepted == False:
            email_text += ('declined (due to reason: ' 
                           + assignment_refusal_reasons_dict[cls.invitation.refusal_reason] + ') ')
        email_text += ('to referee Submission\n\n'
                       + cls.invitation.submission.title + ' by ' 
                       + cls.invitation.submission.author_list + '.')
        if cls.invitation.accepted == False:
            email_text += ('\n\nPlease invite another referee from the Submission\'s editorial page '
                           'at https://scipost.org/submissions/editorial_page/' 
                           + str(cls.invitation.submission.id) + '.')
        email_text += ('\n\nMany thanks for your collaboration,'
                       '\n\nThe SciPost Team.')
        
        emailmessage = EmailMessage(
            email_subject, email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.invitation.submission.editor_in_charge.user.email],
            ['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
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
                      'https://scipost.org/personal_page/ under the Editorial Actions tab.')
        email_text += ('\n\nMany thanks for your collaboration,' +
                       '\n\nThe SciPost Team.')
        
        emailmessage = EmailMessage(
            'SciPost: Report delivered', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.report.submission.editor_in_charge.user.email],
            ['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.send(fail_silently=False)


    @classmethod
    def acknowledge_report_email(cls):
        """ Requires loading 'report' attribute. """
        email_text = ('Dear ' + title_dict[cls.report.author.title] + ' ' +
                      cls.report.author.user.last_name + ','
                      '\n\nMany thanks for your Report on Submission\n\n' +
                       cls.report.submission.title + ' by ' + cls.report.submission.author_list + '.')
        if cls.report.status == 1:
            email_text += ('\n\nYour Report has been vetted through and is viewable at '
                           'https://scipost.org/submissions/' + str(cls.report.submission.id) + '.')
        else:
            email_text += ('\n\nYour Report has been reviewed by the Editor-in-charge of the Submission, '
                           'who decided not to admit it for online posting, citing the reason: '
                           + report_refusal_choices_dict[int(cls.report.status)] + '.'
                           ' We copy the text entries of your report below for your convenience, '
                           'if ever you wish to reformulate it and resubmit it.')
        email_text += ('\n\nMany thanks for your collaboration,' +
                       '\n\nThe SciPost Team.')
        if cls.report.status != 1:
            if cls.email_response is not None:
                email_text += '\n\nAdditional info from the Editor-in-charge: \n'
                email_text += cls.email_response
            email_text += ('\n\nThe text entries of your Report: ' +
                           '\n\nStrengths: \n' + cls.report.strengths +
                           '\n\nWeaknesses: \n' + cls.report.weaknesses +
                           '\n\nReport: \n' + cls.report.report +
                           '\n\nRequested changes: \n' + cls.report.requested_changes +
                           '\n\nRemarks for Editors: \n' + cls.report.remarks_for_editors)
        
        emailmessage = EmailMessage(
            'SciPost: Report acknowledgement', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.report.author.user.email],
            [cls.report.submission.editor_in_charge.user.email, 'submissions@scipost.org'], # bcc EIC
            reply_to=['submissions@scipost.org'])
        emailmessage.send(fail_silently=False)
        

    @classmethod
    def send_author_report_received_email(cls):
        """ Requires loading 'report' attribute. """
        email_text = ('Dear ' + title_dict[cls.report.submission.submitted_by.title] + ' ' +
                      cls.report.submission.submitted_by.user.last_name +
                      ', \n\nA Report has been posted on your recent Submission to SciPost,\n\n' +
                      cls.report.submission.title + ' by ' + cls.report.submission.author_list + '.'
                      '\n\nYou can view it at the Submission Page '
                      'https://scipost.org/submission/' + str(cls.report.submission.id) + '.'
                      '\n\nWe thank you very much for your contribution.'
                      '\n\nSincerely,' +
                      '\n\nThe SciPost Team.')
        emailmessage = EmailMessage(
            'SciPost: Report received on your Submission', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.report.submission.submitted_by.user.email],
            ['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.send(fail_silently=False)

        
    @classmethod
    def send_author_comment_received_email(cls):
        """ Requires loading 'submission' attribute. """
        email_text = ('Dear ' + title_dict[cls.submission.submitted_by.title] + ' ' +
                      cls.submission.submitted_by.user.last_name +
                      ', \n\nA Comment has been posted on your recent Submission to SciPost,\n\n' +
                      cls.submission.title + ' by ' + cls.submission.author_list + '.'
                      '\n\nYou can view it at the Submission Page '
                      'https://scipost.org/submission/' + str(cls.submission.id) + '.'
                      '\n\nWe thank you very much for your contribution.'
                      '\n\nSincerely,' +
                      '\n\nThe SciPost Team.')
        emailmessage = EmailMessage(
            'SciPost: Comment received on your Submission', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.submission.submitted_by.user.email],
            ['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
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
            further_action_page = ('https://scipost.org/submission/editorial_page/' +
                                   str(cls.communication.submission.id))
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
                      cls.communication.submission.title + ' by ' + cls.communication.submission.author_list + '.'
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
