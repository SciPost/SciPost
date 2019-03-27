__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.exceptions import PermissionDenied
from django.db.models import Q

from ajax_select import register, LookupChannel

from ..models import Organization


@register('organization_lookup')
class OrganizationLookup(LookupChannel):
    model = Organization

    def get_query(self, q, request):
        return (self.model.objects.order_by('name')
                .filter(Q(name__icontains=q) |
                        Q(acronym__icontains=q) |
                        Q(name_original__icontains=q))[:10])

    def format_item_display(self, item):
        """(HTML) format item for displaying item in the selected deck area."""
        return u"<span class='auto_lookup_display'>%s</span>" % item.full_name_with_acronym

    def format_match(self, item):
        """(HTML) Format item for displaying in the dropdown."""
        return item.full_name_with_acronym

    def check_auth(self, request):
        """Allow use by logged-in users (e.g. for Affiliations handling)."""
        if not request.user.is_authenticated():
            raise PermissionDenied
