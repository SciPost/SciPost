__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory

# import pytz
# import random

from .models import MailLog, MAIL_NOT_RENDERED, MAIL_RENDERED

# from faker import Faker


class MailLogFactory(factory.django.DjangoModelFactory):
    processed = False
    status = MAIL_NOT_RENDERED
    body = ""
    body_html = ""

    from_email = factory.Faker("ascii_safe_email")
    mail_code = factory.Faker("slug")
    subject = factory.Faker("word")
    to_recipients = factory.List([factory.Faker("ascii_safe_email") for _ in range(2)])
    cc_recipients = factory.List([factory.Faker("ascii_safe_email") for _ in range(2)])
    bcc_recipients = factory.List([factory.Faker("ascii_safe_email") for _ in range(2)])

    class Meta:
        model = MailLog


class RenderedMailLogFactory(MailLogFactory):
    processed = True
    status = MAIL_RENDERED
    body = factory.Faker("text")
    body_html = factory.Faker("text")
