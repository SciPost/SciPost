__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django import forms
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core import serializers
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from guardian.decorators import permission_required_or_403
from guardian.mixins import PermissionRequiredMixin
from guardian.shortcuts import (
    assign_perm,
    remove_perm,
    get_objects_for_user,
    get_perms,
    get_users_with_perms,
    get_groups_with_perms,
)

from .models import Forum, Meeting, Post, Motion
from .forms import (
    ForumForm,
    ForumGroupPermissionsForm,
    ForumOrganizationPermissionsForm,
    MeetingForm,
    PostForm,
    MotionForm,
)

from scipost.mixins import PermissionsMixin


class ForumCreateView(PermissionsMixin, CreateView):
    permission_required = "forums.add_forum"
    model = Forum
    form_class = ForumForm
    template_name = "forums/forum_form.html"
    success_url = reverse_lazy("forums:forums")

    def get_initial(self):
        initial = super().get_initial()
        parent_model = self.kwargs.get("parent_model")
        parent_content_type = None
        parent_object_id = self.kwargs.get("parent_id")
        if parent_model == "forum":
            parent_content_type = ContentType.objects.get(
                app_label="forums", model="forum"
            )
        initial.update(
            {
                "moderators": self.request.user,
                "parent_content_type": parent_content_type,
                "parent_object_id": parent_object_id,
            }
        )
        return initial


class MeetingCreateView(ForumCreateView):
    model = Meeting
    form_class = MeetingForm


class ForumUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "forums.update_forum"
    template_name = "forums/forum_form.html"

    def get_object(self, queryset=None):
        try:
            return Meeting.objects.get(slug=self.kwargs["slug"])
        except Meeting.DoesNotExist:
            return Forum.objects.get(slug=self.kwargs["slug"])

    def get_form(self, form_class=None):
        try:
            self.object.meeting
            return MeetingForm(**self.get_form_kwargs())
        except Meeting.DoesNotExist:
            return ForumForm(**self.get_form_kwargs())


class ForumDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = "forums.delete_forum"
    model = Forum
    success_url = reverse_lazy("forums:forums")

    def delete(self, request, *args, **kwargs):
        """
        A Forum can only be deleted if it does not have any descendants.
        Upon deletion, all object-level permissions associated to the
        Forum are explicitly removed, to avoid orphaned permissions.
        """
        forum = get_object_or_404(Forum, slug=self.kwargs.get("slug"))
        groups_perms_dict = get_groups_with_perms(forum, attach_perms=True)
        if forum.child_forums.all().count() > 0:
            messages.warning(request, "A Forum with descendants cannot be deleted.")
            return redirect(forum.get_absolute_url())
        for group, perms_list in groups_perms_dict.items():
            for perm in perms_list:
                remove_perm(perm, group, forum)
        return super().delete(request, *args, **kwargs)


class ForumDetailView(PermissionRequiredMixin, DetailView):
    permission_required = "forums.can_view_forum"
    model = Forum
    template_name = "forums/forum_detail.html"

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related(
            "meeting",
        )
        qs = qs.prefetch_related(
            "parent",
            "child_forums",
            "posts__motion",
            "posts__posted_by",
            "motions__posted_by",
            "motions__in_agreement",
            "motions__in_doubt",
            "motions__in_disagreement",
            "motions__in_abstain",
            "motions__eligible_for_voting",
        )
        return qs


class HXForumQuickLinksAllView(PermissionRequiredMixin, DetailView):
    permission_required = "forums.can_view_forum"
    model = Forum
    template_name = "forums/_hx_forum_quick_links_all.html"

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.prefetch_related(
            "posts_all__posted_by",
            "posts__motion",
        )
        return qs


class HXForumQuickLinksFollowupsView(PermissionRequiredMixin, DetailView):
    permission_required = "forums.can_view_forum"
    model = Forum
    template_name = "forums/_hx_forum_quick_links_followups.html"

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.prefetch_related(
            "posts__posted_by",
            "posts__cf_latest_followup_in_hierarchy__posted_by",
        )
        return qs


class HXForumPermissionsView(PermissionRequiredMixin, DetailView):
    permission_required = "forums.add_forum"
    model = Forum
    template_name = "forums/_hx_forum_permissions.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["groups_with_perms"] = get_groups_with_perms(self.object).order_by(
            "name"
        )
        context["users_with_perms"] = get_users_with_perms(
            self.object,
            attach_perms=True,
        )
        return context


class ForumPermissionsView(PermissionRequiredMixin, UpdateView):
    permission_required = "forums.can_change_forum"
    model = Forum
    form_class = ForumGroupPermissionsForm
    template_name = "forums/forum_permissions.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        try:
            context["group"] = Group.objects.get(pk=self.kwargs.get("group_id"))
        except Group.DoesNotExist:
            pass
        return context

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        try:
            group = Group.objects.get(pk=self.kwargs.get("group_id"))
            perms = get_perms(group, self.object)
            initial["groups"] = group.id
            initial["can_view"] = "can_view_forum" in perms
            initial["can_post"] = "can_post_to_forum" in perms
        except Group.DoesNotExist:
            pass
        return initial

    def form_valid(self, form):
        for group in form.cleaned_data["groups"]:
            if form.cleaned_data["can_view"]:
                assign_perm("can_view_forum", group, self.object)
            else:
                remove_perm("can_view_forum", group, self.object)
            if form.cleaned_data["can_post"]:
                assign_perm("can_post_to_forum", group, self.object)
            else:
                remove_perm("can_post_to_forum", group, self.object)
        return super().form_valid(form)


class ForumListView(LoginRequiredMixin, ListView):
    model = Forum
    template_name = "forum_list.html"

    def get_queryset(self):
        queryset = get_objects_for_user(
            self.request.user, "forums.can_view_forum"
        ).anchors().select_related("meeting").prefetch_related(
            "posts" + "__followup_posts" * 3,
            "child_forums__posts" + "__followup_posts" * 7,
        )
        return queryset


class PostCreateView(UserPassesTestMixin, CreateView):
    """
    First step of a two-step Post creation process.
    This view, upon successful POST, redirects to the
    PostConfirmCreateView confirmation view.

    To transfer form data from this view to the next (confirmation) one,
    two session variables are used, ``post_subject`` and ``post_text``.
    """

    model = Post
    form_class = PostForm

    def test_func(self):
        if self.request.user.has_perm("forums.add_forum"):
            return True
        forum = get_object_or_404(Forum, slug=self.kwargs.get("slug"))
        if not self.request.user.has_perm("can_post_to_forum", forum):
            raise PermissionDenied
        # Only allow posting if it's within a Forum, or within an ongoing meeting.
        try:
            if datetime.date.today() > forum.meeting.date_until:
                raise Http404("You cannot Post to a Meeting which is finished.")
            elif datetime.date.today() < forum.meeting.date_from:
                raise Http404(
                    "This meeting has not started yet, please come back later!"
                )
        except Meeting.DoesNotExist:
            pass
        return True

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        parent_model = self.kwargs.get("parent_model")
        parent_object_id = self.kwargs.get("parent_id")
        subject = ""
        if parent_model == "forum":
            parent_content_type = ContentType.objects.get(
                app_label="forums", model="forum"
            )
        elif parent_model == "post":
            parent_content_type = ContentType.objects.get(
                app_label="forums", model="post"
            )
            parent = parent_content_type.get_object_for_this_type(pk=parent_object_id)
            if parent.subject.startswith("Re: ..."):
                subject = parent.subject
            elif parent.subject.startswith("Re:"):
                subject = "%s%s" % ("Re: ...", parent.subject.lstrip("Re:"))
            else:
                subject = "Re: %s" % parent.subject
        else:
            raise Http404
        initial.update(
            {
                "posted_by": self.request.user,
                "posted_on": timezone.now(),
                "parent_content_type": parent_content_type,
                "parent_object_id": parent_object_id,
                "subject": subject,
            }
        )
        return initial

    def form_valid(self, form):
        """
        Save the form data to session variables only, redirect to confirmation view.
        """
        self.request.session["post_subject"] = form.cleaned_data["subject"]
        self.request.session["post_text"] = form.cleaned_data["text"]
        return redirect(
            reverse(
                "forums:post_confirm_create",
                kwargs={
                    "slug": self.kwargs.get("slug"),
                    "parent_model": self.kwargs.get("parent_model"),
                    "parent_id": self.kwargs.get("parent_id"),
                },
            )
        )


class MotionCreateView(PostCreateView):
    """
    Specialization of PostCreateView to Motion-class objects.

    By default, all users who can create a Post on the associated
    Forum are given voting rights.
    """

    model = Motion
    form_class = MotionForm
    template_name = "forums/motion_form.html"

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        forum = get_object_or_404(Forum, slug=self.kwargs.get("slug"))
        voters = get_users_with_perms(forum)
        ineligible_ids = []
        for voter in voters.all():
            if not voter.has_perm("can_post_to_forum", forum):
                ineligible_ids.append(voter.id)
        initial.update(
            {
                "eligible_for_voting": voters.exclude(id__in=ineligible_ids),
            }
        )
        return initial

    def form_valid(self, form):
        """
        Save the form data to session variables only, redirect to confirmation view.
        """
        self.request.session["post_subject"] = form.cleaned_data["subject"]
        self.request.session["post_text"] = form.cleaned_data["text"]
        self.request.session["eligible_for_voting_ids"] = list(
            form.cleaned_data["eligible_for_voting"].values_list("pk", flat=True)
        )
        self.request.session["voting_deadline_year"] = form.cleaned_data[
            "voting_deadline"
        ].year
        self.request.session["voting_deadline_month"] = form.cleaned_data[
            "voting_deadline"
        ].month
        self.request.session["voting_deadline_day"] = form.cleaned_data[
            "voting_deadline"
        ].day
        return redirect(
            reverse(
                "forums:motion_confirm_create",
                kwargs={
                    "slug": self.kwargs.get("slug"),
                    "parent_model": self.kwargs.get("parent_model"),
                    "parent_id": self.kwargs.get("parent_id"),
                },
            )
        )


class PostConfirmCreateView(PostCreateView):
    """
    Second (confirmation) step of Post creation process.

    Upon successful POST, the Post object is saved and the
    two session variables ``post_subject`` and ``post_text`` are deleted.
    """

    form_class = PostForm
    template_name = "forums/post_confirm_create.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["subject"].widget = forms.HiddenInput()
        form.fields["text"].widget = forms.HiddenInput()
        return form

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        initial.update(
            {
                "subject": self.request.session.get("post_subject"),
                "text": self.request.session.get("post_text"),
            }
        )
        return initial

    def form_valid(self, form):
        """
        After deleting the session variables used for the confirmation step,
        simply perform the form_valid calls of form_valid from ancestor classes
        ModelFormMixin and FormMixin, due to the fact that the form_valid
        method in the PostCreateView superclass was overriden to a redirect.
        """
        del self.request.session["post_subject"]
        del self.request.session["post_text"]
        self.object = form.save()
        return redirect(self.get_success_url())


class MotionConfirmCreateView(PostConfirmCreateView):
    """
    Specialization of PostConfirmCreateView to Motion-class objects.
    """

    form_class = MotionForm
    template_name = "forums/motion_confirm_create.html"

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        voting_deadline = datetime.date(
            self.request.session.get("voting_deadline_year"),
            self.request.session.get("voting_deadline_month"),
            self.request.session.get("voting_deadline_day"),
        )
        eligible_for_voting_ids = self.request.session.get("eligible_for_voting_ids")
        eligible_for_voting = User.objects.filter(id__in=eligible_for_voting_ids)
        initial.update(
            {
                "eligible_for_voting": eligible_for_voting,
                "voting_deadline": voting_deadline,
            }
        )
        return initial

    def form_valid(self, form):
        del self.request.session["eligible_for_voting_ids"]
        del self.request.session["voting_deadline_year"]
        del self.request.session["voting_deadline_month"]
        del self.request.session["voting_deadline_day"]
        self.object = form.save()
        return super().form_valid(form)


@permission_required_or_403("forums.can_post_to_forum", (Forum, "slug", "slug"))
def motion_vote(request, slug, motion_id, vote):
    motion = get_object_or_404(Motion, pk=motion_id)
    if datetime.date.today() > motion.voting_deadline:
        messages.warning(request, "The voting deadline on this Motion has passed.")
    elif motion.eligible_for_voting.filter(pk=request.user.id).exists():
        motion.in_agreement.remove(request.user)
        motion.in_doubt.remove(request.user)
        motion.in_disagreement.remove(request.user)
        motion.in_abstain.remove(request.user)
        if vote == "Y":
            motion.in_agreement.add(request.user)
        elif vote == "M":
            motion.in_doubt.add(request.user)
        elif vote == "N":
            motion.in_disagreement.add(request.user)
        elif vote == "A":
            motion.in_abstain.add(request.user)
        else:
            raise Http404
        motion.save()
    else:
        messages.warning(request, "You do not have voting rights on this Motion.")
    return redirect(motion.get_absolute_url())
