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
