import datetime

from django.core.mail import EmailMessage

from scipost.models import title_dict

from submissions.models import EditorialAssignment
from submissions.models import assignment_refusal_reasons_dict
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
        email_text = ('Dear ' + title_dict[cls.assignment.to.title] + ' ' +
                      cls.assignment.to.user.last_name +
                      ', \n\nThank you for accepting to become Editor-in-charge of the SciPost Submission\n\n' +
                      cls.assignment.submission.title + ' by ' + cls.assignment.submission.author_list + '.' +
                      '\n\nYou can take your editorial actions from the editorial page '
                      'https://scipost.org/submission/editorial_page/' + str(cls.assignment.submission.id) +
                      ' (also accessible from your personal page https://scipost.org/personal_page under the Editorial Actions tab). '
                      'In particular, you should now invite 3 referees; you might want to make sure you are aware of the '
                      'detailed procedure described in the Editorial College by-laws at https://scipost.org/EdCol_by-laws.'
                      '\n\nMany thanks in advance for your collaboration,' +
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
        email_text = ('Dear ' + title_dict[cls.assignment.submission.submitted_by.title] + ' ' +
                      cls.assignment.submission.submitted_by.user.last_name +
                      ', \n\nWe are pleased to inform you that your recent Submission to SciPost,\n\n' +
                      cls.assignment.submission.title + ' by ' + cls.assignment.submission.author_list +
                      '\n\nhas successfully passed the pre-screening stage. '
                      '\n\nA Submission Page has been activated at '
                      'https://scipost.org/submission/' + str(cls.assignment.submission.id) +
                      ' and a refereeing round has been started, with deadline '
                      'currently set at ' + datetime.datetime.strftime(cls.assignment.submission.reporting_deadline, "%Y-%m-%d") +
                      '. '
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
        email_text = ('Dear ' + title_dict[cls.submission.submitted_by.title] + ' ' +
                      cls.submission.submitted_by.user.last_name +
                      ', \n\nYou recent Submission to SciPost,\n\n' +
                      cls.submission.title + ' by ' + cls.submission.author_list +
                      '\n\nhas unfortunately not passed the pre-screening stage. '
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
        email_text = ('Dear ' + title_dict[cls.invitation.referee.title] + ' ' +
                      cls.invitation.referee.user.last_name +
                      ', \n\nWe have received a Submission to SciPost '
                      'which, in view of your expertise, we would like to invite you to referee:\n\n' +
                      cls.invitation.submission.title + ' by ' + cls.invitation.submission.author_list +
                      ' (see https://scipost.org/submission/' + str(cls.invitation.submission.id) + ').'
                      '\n\nPlease visit https://scipost.org/submissions/accept_or_decline_ref_invitations '
                      '(login required) as soon as possible (ideally within the next 2 days) '
                      'in order to accept or decline this invitation.'
                      '\n\nIf you accept, your report can be submitted by simply clicking on the "Contribute a Report" link at '
                      'https://scipost.org/submission/' + str(cls.invitation.submission.id) + ' before the reporting deadline '
                      '(currently set at ' + datetime.datetime.strftime(cls.invitation.submission.reporting_deadline, "%Y-%m-%d") +
                      '; your report will be automatically recognized as an invited report). You might want to '
                      'make sure you are familiar with our refereeing code of conduct '
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
    def email_referee_response_to_EIC(cls):
        email_text = ('Dear ' + title_dict[cls.invitation.submission.editor_in_charge.title] + ' ' +
                      cls.invitation.submission.editor_in_charge.user.last_name + ','
                      '\n\nReferee ' + title_dict[cls.invitation.referee.title] + ' ' +
                      cls.invitation.referee.user.last_name + ' has ')
        email_subject = 'SciPost: referee declines to review'
        if cls.invitation.accepted:
            email_text += 'accepted '
            email_subject = 'SciPost: referee accepts to review'
        elif cls.invitation.accepted == False:
            email_text += 'declined (due to reason: ' + assignment_refusal_reasons_dict[cls.invitation.refusal_reason] + ') '
        email_text += ('to referee Submission\n\n' +
                       cls.invitation.submission.title + ' by ' + cls.invitation.submission.author_list + '.')
        if cls.invitation.accepted == False:
            email_text += ('\n\nPlease invite another referee from the Submission\'s editorial page at '
                           'https://scipost.org/submissions/editorial_page/' + str(cls.invitation.submission.id) + '.')
        email_text += ('\n\nMany thanks for your collaboration,' +
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
        email_text = ('Dear ' + title_dict[cls.report.submission.editor_in_charge.title] + ' ' +
                      cls.report.submission.editor_in_charge.user.last_name + ','
                      '\n\nReferee ' + title_dict[cls.report.author.title] + ' ' +
                      cls.report.author.user.last_name +
                      ' has delivered a Report for Submission\n\n' +
                       cls.report.submission.title + ' by ' + cls.report.submission.author_list + '.'
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
        email_text = ('Dear ' + title_dict[cls.submission.submitted_by.title] + ' ' +
                      cls.submission.submitted_by.user.last_name +
                      ', \n\nA Report has been posted on your recent Submission to SciPost,\n\n' +
                      cls.submission.title + ' by ' + cls.submission.author_list + '.'
                      '\n\nYou can view it at the Submission Page '
                      'https://scipost.org/submission/' + str(cls.submission.id) + '.'
                      '\n\nWe thank you very much for your contribution.'
                      '\n\nSincerely,' +
                      '\n\nThe SciPost Team.')
        emailmessage = EmailMessage(
            'SciPost: Report received on your Submission', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.submission.submitted_by.user.email],
            ['submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.send(fail_silently=False)
        
    @classmethod
    def send_author_comment_received_email(cls):
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
