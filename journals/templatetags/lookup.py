__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from ajax_select import register, LookupChannel
from ..models import Publication


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
        return request.user.has_perm('can_create_registration_invitations')
