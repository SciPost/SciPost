__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from .models import Branch, AcademicField, Specialty


def ontology_processor(request):
    """
    Append branches and acad_fields to the context of all views,
    and acad_field if session sets it.
    """
    context = {
        'branches': Branch.objects.all(),
        'acad_fields': AcademicField.objects.all(),
    }
    if request.session.get('acad_field_slug', None):
        context['session_acad_field'] = AcademicField.objects.get(
            slug=request.session.get('acad_field_slug'))
    if request.session.get('specialty_slug', None):
        context['session_specialty'] = Specialty.objects.get(
            slug=request.session.get('specialty_slug'))
    return context
