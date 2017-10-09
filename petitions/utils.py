from common.utils import BaseMailUtil


class PetitionUtils(BaseMailUtil):
    mail_sender = 'petitions@scipost.org'
    mail_sender_title = 'SciPost petitions'

    @classmethod
    def send_SPB_petition_signature_thanks(cls, email_address):
        cls._send_mail(cls, 'SPB_petition_signature_thanks',
                       [email_address],
                       'Thanks for signing')
