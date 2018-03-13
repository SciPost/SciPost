from django.core.management.base import BaseCommand
from django.conf import settings

from ...models import MailLog


class Command(BaseCommand):
    """
    This sends the mails that are not processed, written to the database.
    """
    def add_arguments(self, parser):
        parser.add_argument(
            '--id', type=int, required=False,
            help='The id in the `MailLog` table for a specific mail, Leave blank to send all')

    def send_mails(self, mails):
        from django.core.mail import get_connection, EmailMultiAlternatives

        if hasattr(settings, 'EMAIL_BACKEND_ORIGINAL'):
            backend = settings.EMAIL_BACKEND_ORIGINAL
        else:
            backend = 'django.core.mail.backends.smtp.EmailBackend'
        connection = get_connection(backend=backend, fail_silently=False)
        for db_mail in mails:
            mail = EmailMultiAlternatives(
                db_mail.subject,
                db_mail.body,
                db_mail.from_email,
                db_mail.to_recipients,
                bcc=db_mail.bcc_recipients,
                reply_to=(db_mail.from_email,),
                connection=connection)
            if db_mail.body_html:
                mail.attach_alternative(db_mail.body_html, 'text/html')
            print('mail ' + str(db_mail.id))
        return mail.send()

    def handle(self, *args, **options):
        if options.get('id'):
            mails = MailLog.objects.filter(id=options['id'])
        else:
            mails = MailLog.objects.unprocessed()
        self.send_mails(mails)
