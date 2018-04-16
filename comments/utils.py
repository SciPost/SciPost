__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import os

from common.utils import BaseMailUtil


def validate_file_extention(value, allowed_extentions):
    """Check if a filefield (value) has allowed extentions."""
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    return ext.lower() in allowed_extentions


class CommentUtils(BaseMailUtil):
    mail_sender = 'comments@scipost.org'
    mail_sender_title = 'The SciPost Team'

    @classmethod
    def email_comment_vet_accepted_to_author(cls):
        """Send mail after Comment is vetted: `Accept`.

        Requires loading:
        comment -- Comment
        """
        from submissions.models import Submission, Report

        comment = cls._context['comment']
        send_mail = True
        if isinstance(comment.content_object, Submission):
            send_mail = comment.author not in comment.content_object.authors.all()
        elif isinstance(comment.content_object, Report):
            send_mail = comment.author not in comment.content_object.submission.authors.all()

        if not send_mail:
            return

        cls._send_mail(cls, 'comment_vet_accepted',
                       [comment.author.user.email],
                       'SciPost Comment published')

    @classmethod
    def email_comment_vet_rejected_to_author(cls, email_response=''):
        """Send mail after Comment is vetted: `Reject`.

        Requires loading:
        comment -- Comment
        """
        cls._send_mail(cls, 'comment_vet_rejected',
                       [cls._context['comment'].author.user.email],
                       'SciPost Comment rejected',
                       extra_context={'email_response': email_response})
