__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from colleges.models import College


class CollegeSlugConverter:
    regex = '|'.join([c.slug for c in College.objects.all()])

    def to_python(self, value):
        try:
            return College.objects.get(slug=value)
        except College.DoesNotExist:
            return ValueError
        return value

    def to_url(self, value):
        return value
