__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .models import Branch, AcademicField, Specialty
from .forms import SessionAcademicFieldForm, SessionSpecialtyForm


def ontology_processor(request):
    """
    Append branches and acad_fields to the context of all views,
    and acad_field if session sets it.
    """
    context = {
        'branches': Branch.objects.all(),
        'acad_fields': AcademicField.objects.all(),
    }
    initial_acad_field = {}
    if request.session.get('session_acad_field_slug', None):
        try:
            context['session_acad_field'] = AcademicField.objects.get(
                slug=request.session.get('session_acad_field_slug'))
            initial_acad_field['acad_field_slug'] = request.session.get('session_acad_field_slug')
        except AcademicField.DoesNotExist:
            context['session_acad_field'] = None
    context['session_acad_field_form'] = SessionAcademicFieldForm(initial=initial_acad_field)
    initial_specialty = {}
    # If AcademicField is set, deal with Specialty
    if 'session_acad_field' in context:
        if request.session.get('session_specialty_slug', None):
            try:
                context['session_specialty'] = Specialty.objects.get(
                    slug=request.session.get('session_specialty_slug'))
                initial_specialty['specialty_slug'] = request.session.get('session_specialty_slug')
            except Specialty.DoesNotExist:
                context['session_specialty'] = None
            context['session_specialty_form'] = SessionSpecialtyForm(
                acad_field_slug=request.session['session_acad_field_slug'],
                initial=initial_specialty
            )
    return context
