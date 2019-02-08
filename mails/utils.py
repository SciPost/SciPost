__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .mixins import MailUtilsMixin


class DirectMailUtil(MailUtilsMixin):
    """
    Same templates and json files as the form EmailTemplateForm, but this will directly send
    the mails out, without intercepting and showing the mail editor to the user.
    """

    def __init__(self, mail_code, *args, **kwargs):
        kwargs['mail_code'] = mail_code
        kwargs['instance'] = kwargs.pop('instance', None)
        self.delayed_processing = kwargs.pop('delayed_processing', False)
        super().__init__(*args, **kwargs)
        self.validate()
