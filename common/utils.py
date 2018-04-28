__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from datetime import datetime, timedelta
from django.core.mail import EmailMultiAlternatives
from django.template import loader


"""
Given two datetime parameters, this function returns the
number of complete workdays (defined as weekdays) separating them.
"""
def workdays_between (datetime_from, datetime_until):
    duration = datetime_until - datetime_from
    days = int(duration.total_seconds()//86400)
    weeks = int(days//7)
    daygenerator = (datetime_until - timedelta(x) for x in range(days - 7*weeks))
    print ('days = %s, weeks = %s' % (days, weeks))
    workdays = 5 * weeks + sum(1 for day in daygenerator if day.weekday() < 5)
    return workdays




class BaseMailUtil(object):
    mail_sender = 'no-reply@scipost.org'
    mail_sender_title = ''

    @classmethod
    def load(cls, _dict, request=None):
        cls._context = _dict
        cls._context['request'] = request
        for var_name in _dict:
            setattr(cls, var_name, _dict[var_name])

    def _send_mail(cls, template_name, recipients, subject, extra_bcc=None, extra_context={}):
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
        template = loader.get_template('email/%s.txt' % template_name)
        html_template = loader.get_template('email/%s.html' % template_name)
        cls._context.update(extra_context)
        message = template.render(cls._context)
        html_message = html_template.render(cls._context)
        bcc_list = [cls.mail_sender]
        if extra_bcc:
            bcc_list += extra_bcc
        email = EmailMultiAlternatives(
            'SciPost: ' + subject,  # message,
            message,
            '%s <%s>' % (cls.mail_sender_title, cls.mail_sender),
            recipients,
            bcc=bcc_list,
            reply_to=[cls.mail_sender])
        email.attach_alternative(html_message, 'text/html')
        email.send(fail_silently=False)
