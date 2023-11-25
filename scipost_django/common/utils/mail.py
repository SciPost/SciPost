# MARKED FOR DEPRECATION
from django.core.mail import EmailMultiAlternatives
from common.utils.models import get_current_domain


class BaseMailUtil(object):
    mail_sender = "no-reply@%s" % get_current_domain()
    mail_sender_title = ""

    @classmethod
    def load(cls, _dict, request=None):
        cls._context = _dict
        cls._context["request"] = request
        cls._context["domain"] = get_current_domain()
        for var_name in _dict:
            setattr(cls, var_name, _dict[var_name])

    def _send_mail(
        cls, template_name, recipients, subject, extra_bcc=None, extra_context={}
    ):
        """
        Call this method from a classmethod to send emails.
        The template will have context variables defined appended from the `load` method.

        Arguments:
        template_name -- The .html template to use in the mail. The name be used to get the
                         following two templates:
                            `email/<template_name>.txt` (non-HTML)
                            `email/<template_name>.html`
        recipients -- List of mailaddresses to send to mail to.
        subject -- The subject of the mail.
        """
        template = loader.get_template("email/%s.txt" % template_name)
        html_template = loader.get_template("email/%s.html" % template_name)
        cls._context.update(extra_context)
        message = template.render(cls._context)
        html_message = html_template.render(cls._context)
        bcc_list = [cls.mail_sender]
        if extra_bcc:
            bcc_list += extra_bcc
        email = EmailMultiAlternatives(
            subject,
            message,
            "%s <%s>" % (cls.mail_sender_title, cls.mail_sender),
            recipients,
            bcc=bcc_list,
            reply_to=[cls.mail_sender],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
