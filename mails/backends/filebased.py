from django.conf import settings
from django.core.mail.backends.filebased import EmailBackend as FileBacked
from django.core.mail.message import sanitize_address

from ..models import MailLog


class EmailBackend(FileBacked):
    def write_message(self, message):
        bcc_str = ', '.join(message.bcc).encode()
        self.stream.write(b'Extended Mail FileBasedBackend\n\n')
        self.stream.write(b'Bcc: ' + bcc_str + b'\n')
        super().write_message(message)

    def send_messages(self, email_messages, force_original=False):
        """Write all messages to the stream in a thread-safe way."""
        if force_original:
            return super().send_messages(email_messages)

        if not email_messages:
            return
        msg_count = 0

        try:
            for message in email_messages:
                self.write_message_to_db(message)
                msg_count += 1
        except Exception:
            if not self.fail_silently:
                raise
        return msg_count

    def write_message_to_db(self, email_message):
        if not email_message.recipients():
            return False
        encoding = email_message.encoding or settings.DEFAULT_CHARSET
        from_email = email_message.from_email
        to_recipients = [sanitize_address(addr, encoding) for addr in email_message.to if addr]
        bcc_recipients = [sanitize_address(addr, encoding) for addr in email_message.bcc if addr]
        body = email_message.body
        subject = email_message.subject
        body_html = ''
        for alt in email_message.alternatives:
            if alt[1] == 'text/html':
                body_html += alt[0]

        MailLog.objects.create(
            body=body,
            subject=subject,
            body_html=body_html,
            to_recipients=to_recipients,
            bcc_recipients=bcc_recipients,
            from_email=from_email)
        return True
