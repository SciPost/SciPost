__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from common.utils import BaseMailUtil


class PartnerUtils(BaseMailUtil):
    mail_sender = 'partners@scipost.org'
    mail_sender_title = 'SciPost Supporting Partners'


    @classmethod
    def email_contact_new_for_activation(cls, current_user):
        """
        Email a generic address for a Contact.

        current_contact -- Contact object of the User who activated/created the new Contact object.
        """
        cls._send_mail(cls, 'email_contact_new_for_activation',
                       [cls._context['contact'].user.email],
                       'Welcome to the SciPost Supporting Partner Board',
                       extra_context={'sent_by': current_user})
