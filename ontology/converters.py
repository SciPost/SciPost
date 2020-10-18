__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .models import AcademicField, Specialty


class AcademicFieldSlugConverter:
    regex = '|'.join([a.slug for a in AcademicField.objects.all()])

    def to_python(self, value):
        try:
            return AcademicField.objects.get(slug=value)
        except AcademicField.DoesNotExist:
            return ValueError
        return value

    def to_url(self, value):
        return value


class SpecialtySlugConverter:
    regex = '|'.join([s.slug for s in Specialty.objects.all()])

    def to_python(self, value):
        try:
            return Specialty.objects.get(slug=value)
        except Specialty.DoesNotExist:
            return ValueError
        return value

    def to_url(self, value):
        return value
