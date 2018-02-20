from common.utils import BaseMailUtil


def proofs_id_to_slug(id):
    return int(id) + 8932


def proofs_slug_to_id(slug):
    return int(slug) - 8932


class ProductionUtils(BaseMailUtil):
    mail_sender = 'no-reply@scipost.org'
    mail_sender_title = 'SciPost Production'

    @classmethod
    def email_assigned_invitation_officer(cls):
        """
        Email invitation officer about his/her new assigned stream.
        """
        cls._send_mail(cls, 'email_assigned_invitation_officer',
                       [cls._context['stream'].invitations_officer.user.email],
                       'SciPost: you have a new task')

    @classmethod
    def email_assigned_production_officer(cls):
        """
        Email production officer about his/her new assigned stream.
        """
        cls._send_mail(cls, 'email_assigned_production_officer',
                       [cls._context['stream'].officer.user.email],
                       'SciPost: you have a new task')

    @classmethod
    def email_assigned_supervisor(cls):
        """
        Email production officer about his/her new assigned stream.
        """
        cls._send_mail(cls, 'email_assigned_supervisor',
                       [cls._context['stream'].supervisor.user.email],
                       'SciPost: you have a new supervisory task')
