from django.core.mail import EmailMultiAlternatives
from django.template import loader, Context


class BaseMailUtil(object):
    mail_sender = 'no-reply@scipost.org'
    mail_sender_title = ''

    @classmethod
    def load(cls, _dict):
        cls._context = _dict
        for var_name in _dict:
            setattr(cls, var_name, _dict[var_name])

    def _send_mail(cls, template_name, recipients, subject):
        """
        Call this method from a classmethod to send emails.
        The template will have context variables defined appended from the `load` method.

        Arguments:
        template_name -- The .html template to use in the mail. The name be used to get the
                         following two templates:
                            `email/<template_name>.html` (non-HTML)
                            `email/<template_name>_html.html`
        recipients -- List of mailaddresses to send to mail to.
        subject -- The subject of the mail.
        """
        template = loader.get_template('email/%s.html' % template_name)
        html_template = loader.get_template('email/%s_html.html' % template_name)
        message = template.render(Context(cls._context))
        html_message = html_template.render(Context(cls._context))
        email = EmailMultiAlternatives(
            'SciPost: ' + subject, message, '%s <%s>' % (cls.mail_sender_title, cls.mail_sender),
            recipients, bcc=[cls.mail_sender], reply_to=[cls.mail_sender])
        email.attach_alternative(html_message, 'text/html')
        email.send(fail_silently=False)
