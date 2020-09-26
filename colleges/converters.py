__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls.converters import SlugConverter

from colleges.models import College


class CollegeSlugConverter(SlugConverter):

    def to_python(self, value):
        try:
            return College.objects.get(slug=value).slug
        except College.DoesNotExist:
            return ValueError
        return value

    def to_url(self, value):
        return value
