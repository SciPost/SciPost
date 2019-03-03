__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.urlresolvers import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from .models import Forum
from .forms import ForumForm

from scipost.mixins import PermissionsMixin


class ForumCreateView(PermissionsMixin, CreateView):
    permission_required = 'forums.can_add_forum'
    model = Forum
    form_class = ForumForm
    template_name = 'forums/forum_form.html'
    success_url = reverse_lazy('forums:forums')

    def get_initial(self):
        initial = super().get_initial()
        initial.update({
            'moderators': self.request.user
        })
        return initial


class ForumDetailView(DetailView):
    model = Forum
    template_name = 'forums/forum_detail.html'


class ForumListView(ListView):
    model = Forum
    template_name = 'forum_list.html'
