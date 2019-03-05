__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse_lazy
from django.utils import timezone
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from .models import Forum, Post
from .forms import ForumForm, PostForm

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


class PostCreateView(CreateView):
    model = Post
    form_class= PostForm

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        parent_model = self.kwargs.get('parent_model')
        parent_object_id = self.kwargs.get('parent_id')
        subject = ''
        if parent_model == 'forum':
            parent_content_type = ContentType.objects.get(app_label='forums', model='forum')
        elif parent_model == 'post':
            parent_content_type = ContentType.objects.get(app_label='forums', model='post')
            parent = parent_content_type.get_object_for_this_type(pk=parent_object_id)
            subject = 'Reply to %s' % parent.subject
        initial.update({
            'posted_by': self.request.user,
            'posted_on': timezone.now(),
            'parent_content_type': parent_content_type,
            'parent_object_id': parent_object_id,
            'subject': subject,
        })
        return initial

    def get_success_url(self):
        return reverse_lazy('forums:forums')
