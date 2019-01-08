__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.exceptions import PermissionDenied
from django.db.models import Q

from ajax_select import register, LookupChannel

from ..models import Profile


@register('profile_lookup')
class ProfileLookup(LookupChannel):
    model = Profile

    def get_query(self, q, request):
        return (self.model.objects.order_by('last_name')
                .filter(Q(first_name__icontains=q) |
                        Q(last_name__icontains=q) |
                        Q(emails__email__icontains=q) |
                        Q(orcid_id__icontains=q))[:10])

    def format_item_display(self, item):
        """(HTML) format item for displaying item in the selected deck area."""
        return u"<span class='auto_lookup_display'>%s</span>" % item.__str__()

    def format_match(self, item):
        """(HTML) Format item for displaying in the dropdown."""
        return item.__str__()

    def check_auth(self, request):
        """Check if has prifle administrative permissions."""
        if not request.user.has_perm('scipost.can_view_profiles'):
            raise PermissionDenied
