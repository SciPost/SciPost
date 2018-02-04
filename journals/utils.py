from django.core.mail import EmailMessage

from scipost.utils import EMAIL_FOOTER
from common.utils import BaseMailUtil


class JournalUtils(BaseMailUtil):


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
                      + cls.publication.citation() + '.'
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
    def generate_metadata_DOAJ(cls):
        """ Requires loading 'publication' attribute. """
        md = {
            'bibjson': {
                'author': [{'name': cls.publication.author_list}],
                'title': cls.publication.title,
                'abstract': cls.publication.abstract,
                'year': cls.publication.publication_date.strftime('%Y'),
                'month': cls.publication.publication_date.strftime('%m'),
                'start_page': cls.publication.get_paper_nr(),
                'identifier': [
                    {
                        'type': 'eissn',
                        'id': str(cls.publication.in_issue.in_volume.in_journal.issn)
                    },
                    {
                        'type': 'doi',
                        'id': cls.publication.doi_string
                    }
                ],
                'link': [
                    {
                        'url': cls.request.build_absolute_uri(cls.publication.get_absolute_url()),
                        'type': 'fulltext',
                    }
                ],
                'journal': {
                    'publisher': 'SciPost',
                    'volume': str(cls.publication.in_issue.in_volume.number),
                    'number': str(cls.publication.in_issue.number),
                    'identifier': [{
                        'type': 'eissn',
                        'id': str(cls.publication.in_issue.in_volume.in_journal.issn)
                    }],
                    'license': [
                        {
                            'url': cls.request.build_absolute_uri(
                                cls.publication.in_issue.in_volume.in_journal.get_absolute_url()),
                            'open_access': 'true',
                            'type': cls.publication.get_cc_license_display(),
                            'title': cls.publication.get_cc_license_display(),
                        }
                    ],
                    'language': ['EN'],
                    'title': cls.publication.in_issue.in_volume.in_journal.get_name_display(),
                }
            }
        }
        return md


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
