__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf import settings
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat

from .constants import EXTENTIONS_FILES
from .utils import validate_file_extention


def validate_file_extension(value):
    valid = validate_file_extention(value, EXTENTIONS_FILES)
    if not valid:
        raise ValidationError("Unsupported file extension.")


def validate_max_file_size(value):
    if value.size > int(settings.MAX_UPLOAD_SIZE):
        raise ValidationError(
            "Please keep filesize under %s. Current filesize %s"
            % (filesizeformat(settings.MAX_UPLOAD_SIZE), filesizeformat(value.size))
        )
