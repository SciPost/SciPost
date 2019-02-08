__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.mail.backends.filebased import EmailBackend as FileBacked


class EmailBackend(FileBacked):
    def write_message(self, message):
        bcc_str = ', '.join(message.bcc).encode()
        self.stream.write(b'Extended Mail FileBasedBackend\n\n')
        self.stream.write(b'Bcc: ' + bcc_str + b'\n')
        super().write_message(message)
