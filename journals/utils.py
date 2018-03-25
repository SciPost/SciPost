__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.mail import EmailMessage

from common.utils import BaseMailUtil


class JournalUtils(BaseMailUtil):
    mail_sender = 'edadmin@scipost.org'
    mail_sender_title = 'SciPost Editorial Admin'

    @classmethod
    def send_authors_paper_published_email(cls):
        """ Requires loading 'publication' attribute. """
        email_text = ('Dear '
                      + cls.publication.accepted_submission.submitted_by.get_title_display()
                      + ' ' +
                      cls.publication.accepted_submission.submitted_by.user.last_name +
                      ', \n\nWe are happy to inform you that your Submission to SciPost,\n\n' +
                      cls.publication.accepted_submission.title +
                      ' by ' + cls.publication.accepted_submission.author_list +
                      '\n\nhas been published online with reference '
                      + cls.publication.citation + '.'
                      '\n\nThe publication page is located at the permanent link '
                      'https://scipost.org/' + cls.publication.doi_label + '.'
                      '\n\nThe permanent DOI for your publication is 10.21468/'
                      + cls.publication.doi_label + '.'
                      '\n\nTo facilitate dissemination of your paper, we greatly encourage '
                      'you to update the arXiv Journal-ref with this information.'
                      '\n\nWe warmly congratulate you on this achievement and thank you '
                      'for entrusting us with the task of publishing your research. '
                      '\n\nSincerely,' +
                      '\n\nThe SciPost Team.')
        emailmessage = EmailMessage(
            'SciPost: paper published', email_text,
            'SciPost Editorial Admin <admin@scipost.org>',
            [cls.publication.accepted_submission.submitted_by.user.email,
             'admin@scipost.org'],
            reply_to=['admin@scipost.org'])
        emailmessage.send(fail_silently=False)

    @classmethod
    def email_report_made_citable(cls):
        """ Requires loading 'report' attribute. """
        cls._send_mail(cls, 'email_report_made_citable',
                       [cls._context['report'].author.user.email],
                       'Report made citable')

    @classmethod
    def email_comment_made_citable(cls):
        """ Requires loading 'comment' attribute. """
        cls._send_mail(cls, 'email_comment_made_citable',
                       [cls._context['comment'].author.user.email],
                       'Comment made citable')
