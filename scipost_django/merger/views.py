__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import TemplateView


class BaseComparisonView(PermissionRequiredMixin, TemplateView):
    """
    Abstract view for dealing with comparisons of two objects of the same content type.
    """

    pass
