import os

from common.utils import BaseMailUtil


def validate_file_extention(value, allowed_extentions):
    '''Check if a filefield (value) has allowed extentions.'''
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    return ext.lower() in allowed_extentions


class CommentUtils(BaseMailUtil):
    mail_sender = 'comments@scipost.org'
    mail_sender_title = 'The SciPost Team'

    @classmethod
    def email_comment_vet_accepted_to_author(cls):
        """
        Send mail after Comment is vetted: `Accept`

        Requires loading:
        comment -- Comment
        """
        cls._send_mail(cls, 'comment_vet_accepted',
                       [cls._context['comment'].author.user.email],
                       'SciPost Comment published')

    @classmethod
    def email_comment_vet_rejected_to_author(cls, email_response=''):
        """
        Send mail after Comment is vetted: `Reject`

        Requires loading:
        comment -- Comment
        """
        cls._send_mail(cls, 'comment_vet_rejected',
                       [cls._context['comment'].author.user.email],
                       'SciPost Comment rejected',
                       extra_context={'email_response': email_response})
