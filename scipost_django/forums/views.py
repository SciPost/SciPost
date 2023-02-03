__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
import json

from django import forms
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core import serializers
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, redirect, render
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
    MotionVoteForm,
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


class HX_ForumQuickLinksAllView(PermissionRequiredMixin, DetailView):
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


class HX_ForumQuickLinksFollowupsView(PermissionRequiredMixin, DetailView):
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


class HX_ForumPermissionsView(PermissionRequiredMixin, DetailView):
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
    permission_required = "forums.can_administer_forum"
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
            initial["can_administer"] = "can_administer_forum" in perms
            initial["can_view"] = "can_view_forum" in perms
            initial["can_post"] = "can_post_to_forum" in perms
        except Group.DoesNotExist:
            pass
        return initial

    def form_valid(self, form):
        for group in form.cleaned_data["groups"]:
            if form.cleaned_data["can_administer"]:
                assign_perm("can_administer_forum", group, self.object)
            else:
                remove_perm("can_administer_forum", group, self.object)
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


@permission_required_or_403("forums.can_post_to_forum", (Forum, "slug", "slug"))
def _hx_post_form_button(request, slug, parent_model, parent_id, origin, target, text):
    context = {
        "slug": slug,
        "parent_model": parent_model,
        "parent_id": parent_id,
        "origin": origin,
        "target": target,
        "text": text,
    }
    return render(request, "forums/_hx_post_form_button.html", context)


@permission_required_or_403("forums.can_post_to_forum", (Forum, "slug", "slug"))
def _hx_post_form(request, slug, parent_model, parent_id, origin, target, text):
    forum = get_object_or_404(Forum, slug=slug)
    context = {
        "slug": slug,
        "parent_model": parent_model,
        "parent_id": parent_id,
        "origin": origin,
        "target": target,
        "text": text,
    }
    if request.method == "POST":
        form = PostForm(request.POST, forum=forum)
        if form.is_valid():
            post = form.save()
            thread_initiator = post.get_thread_initiator()
            response = render(
                request,
                "forums/post_card.html",
                context={"forum": forum, "post": thread_initiator},
            )
            # if the parent is a forum, then this is a new Motion or Post,
            # and we keep the requested target and swap (== beforebegin).
            # Otherwise, we retarget to the initiator post, and swap outerHTML.
            # In both cases we refocus the browser after settle.
            if parent_model in ["forum", "meeting"]:
                # trigger new post form closure
                response["HX-Trigger"] = f"newPost-{target}"
                # refocus browser on new post
                response["HX-Trigger-After-Settle"] = json.dumps(
                    {"newPost": f"{target}",}
                )
            else:
                # force rerendering of whole thread from initiator down
                response["HX-Retarget"] = f"#thread-{thread_initiator.id}"
                response["HX-Reswap"] = "outerHTML"
                # refocus browser on initiator
                response["HX-Trigger-After-Settle"] = json.dumps(
                    {"newPost": f"thread-{thread_initiator.id}",}
                )
            print(f'{response["HX-Trigger-After-Settle"] = }')
            return response
    else:
        subject = ""
        if parent_model == "forum":
            parent_content_type = ContentType.objects.get(
                app_label="forums",
                model="forum",
            )
        elif parent_model in ["post", "motion"]:
            parent_content_type = ContentType.objects.get(
                app_label="forums",
                model=parent_model,
            )
            parent = parent_content_type.get_object_for_this_type(pk=parent_id)
            if parent.subject.startswith("Re: ..."):
                subject = parent.subject
            elif parent.subject.startswith("Re:"):
                subject = "%s%s" % ("Re: ...", parent.subject.lstrip("Re:"))
            else:
                subject = "Re: %s" % parent.subject
        else:
            raise Http404
        initial = {
            "posted_by": request.user,
            "posted_on": timezone.now(),
            "parent_content_type": parent_content_type,
            "parent_object_id": parent_id,
            "subject": subject,
        }
        form = PostForm(initial=initial, forum=forum)
    context["form"] = form
    return render(request, "forums/_hx_post_form.html", context)


@permission_required_or_403("forums.can_post_to_forum", (Forum, "slug", "slug"))
def _hx_motion_form_button(request, slug):
    context = { "slug": slug, }
    return render(request, "forums/_hx_motion_form_button.html", context)


@permission_required_or_403("forums.can_post_to_forum", (Forum, "slug", "slug"))
def _hx_motion_form(request, slug):
    forum = get_object_or_404(Forum, slug=slug)
    if request.method == "POST":
        form = MotionForm(request.POST, forum=forum)
        if form.is_valid():
            motion = form.save()
            response = render(
                request,
                "forums/post_card.html",
                context={"forum": forum, "post": motion},
            )
            # trigger new motion form closure
            response["HX-Trigger"] = f"newMotion"
            # refocus browser on new Motion
            response["HX-Trigger-After-Settle"] = json.dumps(
                {"newPost": f"thread-{motion.id}",}
            )
            return response
    else:
        parent_content_type = ContentType.objects.get(
            app_label="forums",
            model="forum",
        )
        voters = get_users_with_perms(forum)
        ineligible_ids = []
        for voter in voters.all():
            if not voter.has_perm("can_post_to_forum", forum):
                ineligible_ids.append(voter.id)
        initial = {
            "posted_by": request.user,
            "posted_on": timezone.now(),
            "parent_content_type": parent_content_type,
            "parent_object_id": forum.id,
            "eligible_for_voting": voters.exclude(id__in=ineligible_ids),
        }
        initial["voting_deadline"] = (
            (forum.meeting.date_until if forum.meeting else timezone.now()) +
            datetime.timedelta(days=7)
        )
        form = MotionForm(initial=initial, forum=forum)
    context = { "slug": slug, "form": form, }
    return render(request, "forums/_hx_motion_form.html", context)


@permission_required_or_403("forums.can_view_forum", (Forum, "slug", "slug"))
def _hx_thread_from_post(request, slug, post_id):
    forum = get_object_or_404(Forum, slug=slug)
    post = Post.objects.filter(pk=post_id).select_related(
        "motion",
        "posted_by",
    ).prefetch_related(
        "parent",
        "followup_posts",
    ).first()
    context = {
        "forum": forum,
        "post": post.motion if hasattr(post, "motion") else post,
    }
    return render(request, "forums/post_card.html", context)



@permission_required_or_403("forums.can_post_to_forum", (Forum, "slug", "slug"))
def _hx_motion_voting(request, slug, motion_id):
    forum = get_object_or_404(Forum, slug=slug)
    motion = get_object_or_404(Motion, pk=motion_id)
    initial = {
        "user": request.user.id,
        "motion": motion.id,
    }
    form = MotionVoteForm(request.POST or None, initial=initial)
    if form.is_valid():
        form.save()
        motion.refresh_from_db()
    context = { "forum": forum, "motion": motion, "form": form }
    return render(request, "forums/_hx_motion_voting.html", context)
