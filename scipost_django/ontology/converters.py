__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db.utils import ProgrammingError


class AcademicFieldSlugConverter:
    def __init__(self):
        try:
            from ontology.models import AcademicField

            self.regex = "|".join([a.slug for a in AcademicField.objects.all()])
        except ProgrammingError:
            self.regex = "physics"

    def to_python(self, value):
        from ontology.models import AcademicField

        try:
            return AcademicField.objects.get(slug=value)
        except AcademicField.DoesNotExist:
            return ValueError
        return value

    def to_url(self, value):
        return value


class SpecialtySlugConverter:
    def __init__(self):
        try:
            from ontology.models import Specialty

            self.regex = "|".join([s.slug for s in Specialty.objects.all()])
        except ProgrammingError:
            self.regex = "phys-ct"

    def to_python(self, value):
        from ontology.models import Specialty

        try:
            return Specialty.objects.get(slug=value)
        except Specialty.DoesNotExist:
            return ValueError
        return value

    def to_url(self, value):
        return value
