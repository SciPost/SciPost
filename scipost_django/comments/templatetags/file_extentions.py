__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

from ..constants import EXTENTIONS_IMAGES, EXTENTIONS_PDF
from ..utils import validate_file_extention


register = template.Library()


@register.filter
def is_image(value):
    return validate_file_extention(value, EXTENTIONS_IMAGES)


@register.filter
def is_pdf(value):
    return validate_file_extention(value, EXTENTIONS_PDF)
