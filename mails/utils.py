__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .core import MailEngine


class DirectMailUtil:
    """Send a templated email directly; easiest possible way."""

    def __init__(self, mail_code, delayed_processing=True, **kwargs):
        # Set the data as initials
        self.engine = MailEngine(mail_code, **kwargs)
        self.engine.validate(render_template=not delayed_processing)

    def send_mail(self):
        return self.engine.send_mail()
