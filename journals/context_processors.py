__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from scipost.constants import SCIPOST_DISCIPLINES
from ontology.models import Branch, AcademicField
from .models import Journal


def journals_processor(request):
    """Append all Journals to the context of all views."""
    return {
        'branches': Branch.objects.all(),
        'acad_fields': AcademicField.objects.all(),
        'scipost_disciplines': SCIPOST_DISCIPLINES,
        'journals': Journal.objects.order_by('name')
    }
