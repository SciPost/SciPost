__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .models import Branch, AcademicField, Specialty
from .forms import SessionAcademicFieldForm


def ontology_processor(request):
    """
    Append branches and acad_fields to the context of all views,
    and acad_field if session sets it.
    """
    context = {
        'branches': Branch.objects.all(),
        'acad_fields': AcademicField.objects.all(),
    }
    initial = {}
    if request.session.get('session_acad_field_slug', None):
        try:
            context['session_acad_field'] = AcademicField.objects.get(
                slug=request.session.get('session_acad_field_slug'))
            initial['acad_field_slug'] = request.session.get('session_acad_field_slug')
        except AcademicField.DoesNotExist:
            context['session_acad_field'] = None
    context['session_acad_field_form'] = SessionAcademicFieldForm(initial=initial)
    return context
