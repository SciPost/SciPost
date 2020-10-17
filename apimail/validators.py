__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import string

from django.conf import settings
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat


def _simple_domain_name_validator(value):
    """
    Validate that the given value contains no whitespaces to prevent common typos.

    Taken from django.contrib.sites.models
    """
    checks = ((s in value) for s in string.whitespace)
    if any(checks):
        raise ValidationError(
            "The domain name cannot contain any spaces or tabs.",
            code='invalid',
        )


def validate_max_email_attachment_file_size(value):
    if value.size > int(settings.MAX_EMAIL_ATTACHMENT_FILE_SIZE):
        raise ValidationError(
            'Please keep filesize under %s. Current filesize: %s' % (
                filesizeformat(settings.MAX_EMAIL_ATTACHMENT_FILE_SIZE),
                filesizeformat(value.size))
        )
