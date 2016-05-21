import datetime

from django.core.mail import EmailMessage

from scipost.models import title_dict

from submissions.models import EditorialAssignment
from submissions.models import assignment_refusal_reasons_dict


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
                                    .filter(submission=cls.submission, accepted=None))
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
                      ' (also accessible from your personal page https://scipost.org/personal_page under the Editorial Actions tab).'
                      '\n\nMany thanks in advance for your collaboration,' +
                      '\n\nThe SciPost Team.')
        emailmessage = EmailMessage(
            'SciPost: assignment as EIC', email_text,
            'SciPost Editorial Admin <submissions@scipost.org>',
            [cls.assignment.to.user.email, 'submissions@scipost.org'],
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
            [cls.submission.submitted_by.user.email, 'submissions@scipost.org'],
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
            [cls.invitation.referee.user.email, 'submissions@scipost.org'],
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
            [cls.invitation.submission.editor_in_charge.user.email, 'submissions@scipost.org'],
            reply_to=['submissions@scipost.org'])
        emailmessage.send(fail_silently=False)

