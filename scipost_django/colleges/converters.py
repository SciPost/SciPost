__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db.utils import ProgrammingError


class CollegeSlugConverter:

    def __init__(self):
        try:
            from colleges.models import College
            self.regex = '|'.join([c.slug for c in College.objects.all()])
        except ProgrammingError:
            self.regex = 'physics'

    def to_python(self, value):
        from colleges.models import College
        try:
            return College.objects.get(slug=value)
        except College.DoesNotExist:
            return ValueError
        return value

    def to_url(self, value):
        return value
