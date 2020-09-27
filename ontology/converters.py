__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls.converters import SlugConverter

from .models import Specialty


class SpecialtySlugConverter(SlugConverter):

    def to_python(self, value):
        try:
            return Specialty.objects.get(slug=value)
        except Specialty.DoesNotExist:
            return ValueError
        return value

    def to_url(self, value):
        return value
