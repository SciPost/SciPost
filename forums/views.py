__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.models import Group
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse_lazy
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from guardian.mixins import PermissionRequiredMixin
from guardian.shortcuts import (assign_perm, remove_perm,
    get_objects_for_user, get_perms, get_users_with_perms, get_groups_with_perms)

from .models import Forum, Post
from .forms import ForumForm, ForumGroupPermissionsForm, ForumOrganizationPermissionsForm, PostForm

from scipost.mixins import PermissionsMixin


class ForumCreateView(PermissionsMixin, CreateView):
    permission_required = 'forums.add_forum'
    model = Forum
    form_class = ForumForm
    template_name = 'forums/forum_form.html'
    success_url = reverse_lazy('forums:forums')

    def get_initial(self):
        initial = super().get_initial()
        parent_model = self.kwargs.get('parent_model')
        parent_content_type = None
        parent_object_id = self.kwargs.get('parent_id')
        if parent_model == 'forum':
            parent_content_type = ContentType.objects.get(app_label='forums', model='forum')
        initial.update({
            'moderators': self.request.user,
            'parent_content_type': parent_content_type,
            'parent_object_id': parent_object_id,
        })
        return initial


class ForumDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'forums.can_view_forum'
    model = Forum
    template_name = 'forums/forum_detail.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['groups_with_perms'] = get_groups_with_perms(self.object).order_by('name')
        context['users_with_perms'] = get_users_with_perms(self.object)
        context['group_permissions_form'] = ForumGroupPermissionsForm()
        context['organization_permissions_form'] = ForumOrganizationPermissionsForm()
        return context


class ForumPermissionsView(PermissionRequiredMixin, UpdateView):
    permission_required = 'forums.can_change_forum'
    model = Forum
    form_class = ForumGroupPermissionsForm
    template_name = 'forums/forum_permissions.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        try:
            context['group'] = Group.objects.get(pk=self.kwargs.get('group_id'))
        except Group.DoesNotExist:
            pass
        return context

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        try:
            group = Group.objects.get(pk=self.kwargs.get('group_id'))
            perms = get_perms (group, self.object)
            initial['group'] = group.id
            initial['can_view'] = 'can_view_forum' in perms
            initial['can_post'] = 'can_post_to_forum' in perms
        except Group.DoesNotExist:
            pass
        return initial

    def form_valid(self, form):
        if form.cleaned_data['can_view']:
            assign_perm('can_view_forum', form.cleaned_data['group'], self.object)
        else:
            remove_perm('can_view_forum', form.cleaned_data['group'], self.object)
        if form.cleaned_data['can_post']:
            assign_perm('can_post_to_forum', form.cleaned_data['group'], self.object)
        else:
            remove_perm('can_post_to_forum', form.cleaned_data['group'], self.object)
        return super().form_valid(form)


class ForumListView(ListView):
    model = Forum
    template_name = 'forum_list.html'

    def get_queryset(self):
        queryset = get_objects_for_user(self.request.user, 'forums.can_view_forum').anchors()
        return queryset


class PostCreateView(UserPassesTestMixin, CreateView):
    model = Post
    form_class= PostForm

    def test_func(self):
        if self.request.user.has_perm('forums.add_forum'):
            return True
        forum = get_object_or_404(Forum, slug=self.kwargs.get('slug'))
        if self.request.user.has_perm('can_post_to_forum', forum):
            return True
        else:
            raise PermissionDenied

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
        else:
            raise Http404
        initial.update({
            'posted_by': self.request.user,
            'posted_on': timezone.now(),
            'parent_content_type': parent_content_type,
            'parent_object_id': parent_object_id,
            'subject': subject,
        })
        return initial

    def get_success_url(self):
        return self.object.get_absolute_url()
