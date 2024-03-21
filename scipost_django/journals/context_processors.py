__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from ontology.models import Branch, AcademicField
from .models import Journal, Publication


def publishing_years_processor(request):
    """List of years where publishing activity took place, going backwards in time."""
    return {
        "publishing_years": range(
            Publication.objects.published().first().publication_date.year,
            Publication.objects.published().last().publication_date.year,
            -1,
        )
    }


def journals_processor(request):
    """Append all Journals to the context of all views."""
    return {
        "branches": Branch.objects.all(),
        "acad_fields": AcademicField.objects.all(),
        "journals": Journal.objects.order_by("name"),
    }
