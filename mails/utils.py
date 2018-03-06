from .mixins import MailUtilsMixin


class DirectMailUtil(MailUtilsMixin):
    """
    Same templates and json files as the form EmailTemplateForm, but this will directly send
    the mails out, without intercepting and showing the mail editor to the user.
    """

    def __init__(self, mail_code, instance, *args, **kwargs):
        kwargs['mail_code'] = mail_code
        kwargs['instance'] = instance
        super().__init__(*args, **kwargs)
        self.validate()
