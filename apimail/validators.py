__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf import settings
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat


def validate_max_email_attachment_file_size(value):
    if value.size > int(settings.MAX_EMAIL_ATTACHMENT_FILE_SIZE):
        raise ValidationError(
            'Please keep filesize under %s. Current filesize: %s' % (
                filesizeformat(settings.MAX_EMAIL_ATTACHMENT_FILE_SIZE),
                filesizeformat(value.size))
        )
