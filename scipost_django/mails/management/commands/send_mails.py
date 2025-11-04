from typing import Iterable

from django.core.mail import get_connection
from django.core.management.base import BaseCommand
from django.conf import settings

from ...core import MailEngine
from ...models import MailLog

BULK_EMAIL_THROTTLE = getattr(settings, "BULK_EMAIL_THROTTLE", 5)

if hasattr(settings, "EMAIL_BACKEND_ORIGINAL"):
    backend = settings.EMAIL_BACKEND_ORIGINAL
else:
    # Fallback to Django's default
    backend = "django.core.mail.backends.smtp.EmailBackend"

if backend == "mails.backends.filebased.ModelEmailBackend":
    raise AssertionError("The `EMAIL_BACKEND_ORIGINAL` cannot be the ModelEmailBackend")

connection = get_connection(backend=backend, fail_silently=False)


class Command(BaseCommand):
    """
    This sends the mails that are not processed, written to the database.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--id",
            type=int,
            required=False,
            help="The id in the `MailLog` table for a specific mail, Leave blank to send all",
        )

    def _render_mail(self, mail: MailLog):
        """
        Render the templates for the mail if not done yet.
        """
        engine = MailEngine(mail.mail_code, **mail.get_full_context())
        engine.process(render_template=True)

        MailLog.objects.filter(pk=mail.pk).update(
            body=engine.mail_config.get("message", ""),
            body_html=engine.mail_config.get("html_message", ""),
            subject=engine.mail_config.get("subject", ""),
            status="rendered",
        )

    def _send_mail(self, connection, mail_log: "MailLog", recipients, **kwargs):
        """
        Build and send the mail, returning the response.
        """
        from django.core.mail import EmailMultiAlternatives

        mail = EmailMultiAlternatives(
            mail_log.subject,
            mail_log.body,
            mail_log.from_email,
            recipients,
            connection=connection,
            cc=mail_log.cc_recipients,
            bcc=mail_log.bcc_recipients,
            reply_to=(mail_log.from_email,),
            **kwargs,
        )
        # Attach the HTML version *ONLY* if one exists
        # If attached while empty, it will cause the mail to be treated as if were
        if mail_log.body_html:
            mail.attach_alternative(mail_log.body_html, "text/html")
        response = mail.send()
        return response

    def process_mail_logs(self, mail_logs: "Iterable[MailLog]"):
        """
        Process the MailLogs according to their type and send the mails.
        """
        count = 0
        for mail_log in mail_logs:
            if mail_log.status == "not_rendered":
                self._render_mail(mail_log)
                mail_log.refresh_from_db()

            # If single entry per mail, send regularly
            if mail_log.type == mail_log.TYPE_SINGLE:
                response = self._send_mail(
                    connection,
                    mail_log,
                    mail_log.to_recipients,
                )

                if response:
                    count += 1
                    mail_log.status = "sent"
                    mail_log.processed = True

            # If bulk, build separate instances of the mail
            # for each recipient up to the throttle limit per run
            elif mail_log.type == mail_log.TYPE_BULK:
                if mail_log.sent_to is None:
                    mail_log.sent_to = []
                if mail_log.to_recipients is None:
                    self.stdout.write(
                        "MailLog {} has no recipients. Skipping.".format(mail_log.id)
                    )
                    continue

                remaining_recipients = [
                    recipient
                    for recipient in mail_log.to_recipients
                    if recipient not in mail_log.sent_to
                ]

                # Guard against empty recipients, updating the status
                if not remaining_recipients:
                    mail_log.status = "sent"
                    mail_log.processed = True
                    mail_log.save()
                    continue

                # For each recipient not yet sent to and up to the throttle limit
                for recipient in remaining_recipients[:BULK_EMAIL_THROTTLE]:
                    response = self._send_mail(connection, mail_log, [recipient])

                    if response:
                        count += 1
                        mail_log.sent_to.append(recipient)

            mail_log.save()

        return count

    def handle(self, *args, **options):
        if options.get("id"):
            mail_logs = MailLog.objects.filter(id=options["id"])
        else:
            mail_logs = MailLog.objects.not_sent().order_by("created")[:10]
        nr_mails = self.process_mail_logs(mail_logs)
        self.stdout.write("Sent {} mails.".format(nr_mails))
