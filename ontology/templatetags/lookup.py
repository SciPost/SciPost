__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.exceptions import PermissionDenied
from django.shortcuts import render, reverse

from ajax_select import register, LookupChannel

from ..models import Topic


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


@register('linked_topic_lookup')
class LinkedTopicLookup(LookupChannel):
    model = Topic

    def get_query(self, q, request):
        return (self.model.objects.filter(name__icontains=q)[:10])

    def format_item_display(self, item):
        return

    def format_match(self, item):
        return "<span class='auto_lookup_display'><a href='%s'>%s</a></span>" % (
            reverse('ontology:topic_details', kwargs={'slug': item.slug}), item)

    def check_auth(self, request):
        pass
