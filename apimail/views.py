__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.views.generic.list import ListView

from .models import StoredMessage


class StoredMessageListView(ListView):
    model = StoredMessage
    template_name = 'apimail/message_list.html'

    def get_queryset(self):
        return StoredMessage.objects.filter_for_user(self.request.user)
