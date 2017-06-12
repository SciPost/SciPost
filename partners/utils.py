from common.utils import BaseMailUtil



class PartnerUtils(BaseMailUtil):
    mail_sender = 'partners@scipost.org'
    mail_sender_title = 'SciPost Supporting Partners'

    @classmethod
    def email_prospartner_contact(cls):
        """
        Email a contact of a ProspectivePartner,
        for example to establish a first contact
        and invite participation to the Supporting Partners Board.
        """
        cls._send_mail(cls, 'email_prospartner_contact',
                       [cls._context['contact'].email,],
                        cls._context['email_subject'])
