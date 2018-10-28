__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.exceptions import PermissionDenied

from ajax_select import register, LookupChannel

from ..models import Tag, Topic


@register('tag_lookup')
class TagLookup(LookupChannel):
    model = Tag

    def get_query(self, q, request):
        return (self.model.objects.filter(name__icontains=q)[:10])

    def format_item_display(self, item):
        return "<span class='auto_lookup_display'>%s</span>" % item

    def format_match(self, item):
        return item.name

    def check_auth(self, request):
        if not request.user.has_perm('scipost.can_manage_ontology'):
            raise PermissionDenied


@register('topic_lookup')
class TopicLookup(LookupChannel):
    model = Topic

    def get_query(self, q, request):
        return (self.model.objects.filter(name__icontains=q)[:10])

    def format_item_display(self, item):
        return "<span class='auto_lookup_display'>%s</span>" % item

    def format_match(self, item):
        return item.name

    def check_auth(self, request):
        if not request.user.has_perm('scipost.can_manage_ontology'):
            raise PermissionDenied
