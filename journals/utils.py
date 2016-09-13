from django.core.mail import EmailMessage

from scipost.models import title_dict

class JournalUtils(object):

    @classmethod
    def load(cls, dict):
        for var_name in dict:
            setattr(cls, var_name, dict[var_name])


    @classmethod
    def send_authors_paper_published_email(cls):
        """ Requires loading 'publication' attribute. """
        email_text = ('Dear ' 
                      + title_dict[cls.publication.accepted_submission.submitted_by.title] 
                      + ' ' +
                      cls.publication.accepted_submission.submitted_by.user.last_name +
                      ', \n\nWe have happy to inform you that your Submission to SciPost,\n\n' +
                      cls.publication.accepted_submission.title + 
                      ' by ' + cls.publication.accepted_submission.author_list +
                      '\n\nhas been published online with reference '
                      + cls.publication.citation() + '.'
                      '\n\nThe publication page is located at the permanent link '
                      'https://scipost.org/' + cls.publication.doi_string + '.'
                      '\n\nWe warmly congratulate you on this achievement and thank you '
                      'for entrusting us with the task of publishing your research.'
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
    def generate_metadata_xml_file(cls):
        """ Requires loading 'publication' attribute. """
        
