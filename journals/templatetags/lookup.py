__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.exceptions import PermissionDenied
from django.db.models import Q

from ajax_select import register, LookupChannel

from ..models import Publication

from funders.models import Funder, Grant
from organizations.models import Organization


@register('publication_lookup')
class PublicationLookup(LookupChannel):
    model = Publication

    def get_query(self, q, request):
        return (self.model.objects
                .published()
                .order_by('-publication_date')
                .filter(title__icontains=q)[:10])

    def format_item_display(self, item):
        '''(HTML) format item for displaying item in the selected deck area.'''
        return u"<span class='auto_lookup_display'>%s</span>" % item

    def format_match(self, item):
        '''(HTML) Format item for displaying in the dropdown.'''
        return u"%s (%s)<br><span class='text-muted'>by %s</span>" % (item.title,
                                                                      item.doi_string,
                                                                      item.author_list)

    def check_auth(self, request):
        """
        Check if current user has required permissions.
        Right now only used for draft registration invitations. May be extended in the
        future for other purposes as well.
        """
        if not request.user.has_perm('scipost.can_create_registration_invitations'):
            raise PermissionDenied


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


@register('funder_lookup')
class FunderLookup(LookupChannel):
    model = Funder

    def get_query(self, q, request):
        return self.model.objects.filter(
            Q(name__icontains=q) | Q(acronym__icontains=q) |
            Q(identifier__icontains=q) | Q(organization__name__icontains=q) |
            Q(organization__name_original__icontains=q) |
            Q(organization__acronym__icontains=q)).order_by('name')[:10]

    def format_item_display(self, item):
        """(HTML) format item for displaying item in the selected deck area."""
        return u"<span class='auto_lookup_display'>%s</span>" % str(item)

    def format_match(self, item):
        """(HTML) Format item for displaying in the dropdown."""
        return str(item)

    def check_auth(self, request):
        """Check for required permissions."""
        if not request.user.has_perm('scipost.can_draft_publication'):
            raise PermissionDenied


@register('grant_lookup')
class GrantLookup(LookupChannel):
    model = Grant

    def get_query(self, q, request):
        return (self.model.objects.filter(
            Q(funder__name__icontains=q) | Q(funder__acronym__icontains=q) |
            Q(number__icontains=q) | Q(recipient_name__icontains=q) |
            Q(recipient__user__last_name__icontains=q) |
            Q(recipient__user__first_name__icontains=q) |
            Q(further_details__icontains=q)).order_by('funder__name', 'number')[:10])

    def format_item_display(self, item):
        """(HTML) format item for displaying item in the selected deck area."""
        return u"<span class='auto_lookup_display'>%s</span>" % str(item)

    def format_match(self, item):
        """(HTML) Format item for displaying in the dropdown."""
        return str(item)

    def check_auth(self, request):
        """Check for required permissions."""
        if not request.user.has_perm('scipost.can_draft_publication'):
            raise PermissionDenied
