from common.utils import BaseMailUtil


SPB_PETITION_THANKS = (
    'Many thanks for signing the petition!\n\n'
    'If you have not done so already, you can really further help SciPost convince '
    'your institution, library and/or funding agency to become Supporting Partners '
    'by sending a personalized email to one of their representatives; we have a '
    'handy email template for you to use at https://scipost.org/partners/.\n\n'
    'You can also point them to our prospectus and draft agreement on that same '
    'page.\n\nWe are very grateful for your help.\n\nThe SciPost Team'
    )

SPB_PETITION_THANKS_HTML = (
)


class PetitionUtils(BaseMailUtil):
    mail_sender = 'petitions@scipost.org'
    mail_sender_title = 'SciPost petitions'

    @classmethod
    def send_SPB_petition_signature_thanks(cls, email_address):
        cls._send_mail(cls, 'SPB_petition_signature_thanks',
                       [email_address],
                       'Thanks for signing')
