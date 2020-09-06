__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .models import AcademicField

acad_field_list = [f.slug for f in AcademicField.objects.all()]

ACADEMIC_FIELD_REGEX = '|'.join(acad_field_list)
