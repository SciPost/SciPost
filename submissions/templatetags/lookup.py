from ajax_select import register, LookupChannel
from ..models import Submission


@register('submissions_lookup')
class SubmissionLookup(LookupChannel):
    model = Submission

    def get_query(self, q, request):
        return (self.model.objects
                .public()
                .order_by('-submission_date')
                .filter(title__icontains=q)
                .prefetch_related('publication')[:10])

    def format_item_display(self, item):
        '''(HTML) format item for displaying item in the selected deck area.'''
        return u"<span class='auto_lookup_display'>%s</span>" % item

    def format_match(self, item):
        '''(HTML) Format item for displaying in the dropdown.'''
        return u"%s<br><span class='text-muted'>by %s</span>" % (item.title, item.author_list)
