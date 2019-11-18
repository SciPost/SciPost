__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.models import User, Group

from ajax_select import register, LookupChannel


@register('user_lookup')
class UserLookup(LookupChannel):
    model = User

    def get_query(self, q, request):
        return self.model.objects.filter(last_name__icontains=q)[:10]

    def format_item_display(self, item):
        return "<span class='auto_lookup_display'>%s, %s</span>" % (item.last_name, item.first_name)

    def format_match(self, item):
        return "%s, %s" % (item.last_name, item.first_name)
