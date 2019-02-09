__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


class MailEngine:
    """
    This engine processes the configuration and template files to be saved into the database in
    the MailLog table.
    """

    def __init__(self, mail_code, subject='', recipient_list=None, bcc=None, from_email='',
            from_name=None, **kwargs):
        """
        Start engine with specific mail_code. Any other keyword argument that is passed will
        be used as a variable in the mail template.

        @Arguments
        -- mail_code (str)

        @Keyword arguments
        The following arguments overwrite the default values, set in the configuration files:
        -- subject (str, optional)
        -- recipient_list (str, optional): List of email addresses or db-relations.
        -- bcc (str, optional): List of email addresses or db-relations.
        -- from_email (str, optional): Plain email address.
        -- from_name (str, optional): Display name for from address.
        """
        self.mail_code = mail_code
        self.extra_config = {
            'bcc': [],
            'subject': subject,
            'from_name': from_name,
            'from_email': '',
            'recipient_list': [],
        }
        if from_email:
            if not isinstance(from_email, str):
                raise TypeError('"from_email" argument must be a string')
            self.extra_config['from_email'] = from_email
        if recipient_list:
            if isinstance(recipient_list, str):
                raise TypeError('"recipient_list" argument must be a list or tuple')
            self.extra_config['recipient_list'] = list(recipient_list)
        if bcc:
            if isinstance(bcc, str):
                raise TypeError('"bcc" argument must be a list or tuple')
            self.extra_config['bcc'] = list(bcc)
        self.template_variables = kwargs

    def start(self):
        return True
