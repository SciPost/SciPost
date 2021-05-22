from django.core.management.base import BaseCommand
from django.conf import settings

from ...core import MailEngine
from ...models import MailLog


class Command(BaseCommand):
    """
    This sends the mails that are not processed, written to the database.
    """
    def add_arguments(self, parser):
        parser.add_argument(
            '--id', type=int, required=False,
            help='The id in the `MailLog` table for a specific mail, Leave blank to send all')

    def _process_mail(self, mail):
        """
        Render the templates for the mail if not done yet.
        """
        engine = MailEngine(mail.mail_code, **mail.get_full_context())
        message, html_message = engine.render_only()

        MailLog.objects.filter(id=mail.id).update(
            body=message, body_html=html_message, status='rendered')

    def send_mails(self, mails):
        from django.core.mail import get_connection, EmailMultiAlternatives

        if hasattr(settings, 'EMAIL_BACKEND_ORIGINAL'):
            backend = settings.EMAIL_BACKEND_ORIGINAL
        else:
            # Fallback to Django's default
            backend = 'django.core.mail.backends.smtp.EmailBackend'

        if backend == 'mails.backends.filebased.ModelEmailBackend':
            raise AssertionError('The `EMAIL_BACKEND_ORIGINAL` cannot be the ModelEmailBackend')

        connection = get_connection(backend=backend, fail_silently=False)
        count = 0
        for db_mail in mails:
            if db_mail.status == 'not_rendered':
                self._process_mail(db_mail)
                db_mail.refresh_from_db()

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
            response = mail.send()
            if response:
                count += 1
                db_mail.processed = True
                db_mail.status = 'sent'
                db_mail.save()
        return count

    def handle(self, *args, **options):
        if options.get('id'):
            mails = MailLog.objects.filter(id=options['id'])
        else:
            mails = MailLog.objects.not_sent().order_by('created')[:2]
        nr_mails = self.send_mails(mails)
        self.stdout.write('Sent {} mails.'.format(nr_mails))
