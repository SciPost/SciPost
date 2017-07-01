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
                       [cls._context['contact'].email],
                       cls._context['email_subject'])

    @classmethod
    def email_prospartner_generic(cls):
        """
        Email a generic address for a ProspectivePartner
        for which no Contact could be defined.
        """
        cls._send_mail(cls, 'email_prospartner_contact',
                       [cls._context['email']],
                       cls._context['email_subject'])

    @classmethod
    def email_contact_new_for_activation(cls, current_contact):
        """
        Email a generic address for a Contact.

        current_contact -- Contact object of the User who activated/created the new Contact object.
        """
        cls._send_mail(cls, 'email_contact_new_for_activation',
                       [cls._context['contact'].user.email],
                       'Welcome to the SciPost Supporting Partner Board',
                       extra_context={'created_by': current_contact})
