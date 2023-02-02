__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.db import models
from django.utils import timezone

from .managers import ForumQuerySet, PostQuerySet


class Forum(models.Model):
    """
    A Forum is a discussion location for a defined set of Users.

    A Forum instance can be publicly visible. For publicly invisible forums,
    as well as for thread creation and posting rights,
    access is specified flexibly on a per-Group and/or per-User basis
    via object-level permissions (through the django-guardian required app).

    Forums can be related to parent/children via parent [GenericForeignKey]
    and child_forums [GenericRelation] fields.

    Similarly, Posts in a Forum are listed in the posts [GenericRelation] field.
    """

    name = models.CharField(max_length=256)
    slug = models.SlugField(allow_unicode=True)
    description = models.TextField(
        blank=True,
        null=True,
        help_text=(
            "You can use plain text, Markdown or reStructuredText; see our "
            '<a href="/markup/help/" target="_blank">markup help</a> pages.'
        ),
    )
    publicly_visible = models.BooleanField(default=False)
    moderators = models.ManyToManyField("auth.User", related_name="moderated_forums")

    parent_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, blank=True, null=True
    )
    parent_object_id = models.PositiveIntegerField(blank=True, null=True)
    parent = GenericForeignKey("parent_content_type", "parent_object_id")

    child_forums = GenericRelation(
        "forums.Forum",
        content_type_field="parent_content_type",
        object_id_field="parent_object_id",
        related_query_name="parent_forums",
    )
    posts = GenericRelation(
        "forums.Post",
        content_type_field="parent_content_type",
        object_id_field="parent_object_id",
        related_query_name="parent_forums",
    )
    posts_all = GenericRelation(
        "forums.Post",
        content_type_field="anchor_content_type",
        object_id_field="anchor_object_id",
        related_query_name="anchor_forums",
    )
    motions = GenericRelation(
        "forums.Motion",
        content_type_field="parent_content_type",
        object_id_field="parent_object_id",
        related_query_name="parent_forums",
    )

    # calculated fields
    cf_nr_posts = models.PositiveSmallIntegerField(blank=True, null=True)

    objects = ForumQuerySet.as_manager()

    class Meta:
        ordering = [
            "name",
        ]
        permissions = [
            ("can_view_forum", "Can view Forum"),
            ("can_post_to_forum", "Can add Post to Forum"),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("forums:forum_detail", kwargs={"slug": self.slug})

    def update_cfs(self):
        self.update_cf_nr_posts()
        if self.parent:
            self.parent.update_cfs()

    @property
    def nr_posts(self):
        """Recursively counts the number of posts in this Forum."""
        nr = 0
        for post in self.posts.all():
            nr += post.nr_followups
        if self.posts.all():
            nr += self.posts.all().count()
        return nr

    def update_cf_nr_posts(self):
        self.cf_nr_posts = self.nr_posts
        self.save()

    def posts_hierarchy_id_list(self):
        id_list = []
        for post in self.posts.all():
            id_list += post.posts_hierarchy_id_list()
        return id_list

    @property
    def latest_post(self):
        id_list = self.posts_hierarchy_id_list()
        try:
            return Post.objects.filter(id__in=id_list).order_by("-posted_on").first()
        except:
            return None


class Meeting(Forum):
    """
    A Meeting is a Forum but with fixed start and end dates,
    and with additional descriptor fields (preamble, minutes).

    By definition, adding new Posts is allowed up to and including
    the date specified in ``date_until``. The Meeting can however
    be viewed in perpetuity by users who have viewing rights.
    """

    forum = models.OneToOneField(
        "forums.Forum", on_delete=models.CASCADE, parent_link=True
    )
    date_from = models.DateField()
    date_until = models.DateField()
    preamble = models.TextField(
        help_text=(
            "Explanatory notes for the meeting.\n"
            "You can use plain text, Markdown or reStructuredText; see our "
            '<a href="/markup/help/" target="_blank">markup help</a> pages.'
        )
    )
    minutes = models.TextField(
        blank=True,
        null=True,
        help_text=(
            "To be filled in after completion of the meeting.\n"
            "You can use plain text, Markdown or reStructuredText; see our "
            '<a href="/markup/help/" target="_blank">markup help</a> pages.'
        ),
    )
    objects = models.Manager()

    class Meta:
        ordering = [
            "-date_until",
        ]

    def __str__(self):
        return "%s, [%s to %s]" % (
            self.forum,
            self.date_from.strftime("%Y-%m-%d"),
            self.date_until.strftime("%Y-%m-%d"),
        )

    @property
    def future(self):
        return datetime.date.today() < self.date_from

    @property
    def ongoing(self):
        today = datetime.date.today()
        return today >= self.date_from and today <= self.date_until

    @property
    def past(self):
        return datetime.date.today() > self.date_until

    @property
    def context_colors(self):
        """If meeting is future: primary; ongoing: success; voting: warning; finished: info."""
        today = datetime.date.today()
        if today < self.date_from:
            return {"bg": "primary", "text": "white", "message": "Meeting is coming up"}
        elif today <= self.date_until:
            return {"bg": "success", "text": "light", "message": "Meeting is ongoing"}
        elif today < self.date_until + datetime.timedelta(days=8):
            return {
                "bg": "warning",
                "text": "dark",
                "message": "Meeting is finished, voting open",
            }
        else:
            return {"bg": "info", "text": "dark", "message": "Meeting is finished"}


class Post(models.Model):
    """
    A comment, feedback, question or similar, with a specified parent object.

    If the Post is submitted by Admin, Advisory Board members or Fellows,
    it is marked as not needing vetting before becoming visible.
    Similarly, for Posts created by organizations.Contacts, no vetting is required.
    Otherwise, e.g. for Contributors-submitted Posts to a publicly-visible
    Forum, vetting by Admin is required.

    A Post must have a parent object (represented here as a GenericForeignKey).
    If the parent is a Forum, the Post is interpreted as the head of
    a new discussion thread. If the parent is a Post, then it is interpreted as
    part of an ongoing thread.

    The text field can contain plain text, Markdown or reStructuredText markup,
    auto-recognized via the markup app facilities.
    """

    posted_by = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    posted_on = models.DateTimeField(default=timezone.now)
    needs_vetting = models.BooleanField(default=True)
    vetted_by = models.ForeignKey(
        "auth.User",
        related_name="vetted_posts",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    parent_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    parent_object_id = models.PositiveIntegerField()
    parent = GenericForeignKey("parent_content_type", "parent_object_id")
    followup_posts = GenericRelation(
        "forums.Post",
        content_type_field="parent_content_type",
        object_id_field="parent_object_id",
        related_query_name="parent_posts",
    )
    subject = models.CharField(max_length=256)
    text = models.TextField(
        help_text=(
            "You can use plain text, Markdown or reStructuredText; see our "
            '<a href="/markup/help/" target="_blank">markup help</a> pages.'
        )
    )
    # Accelerators: to avoid navigating the hierarchy of objects
    anchor_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="forum_or_meeting_posts",
    )
    anchor_object_id = models.PositiveIntegerField(blank=True, null=True)
    anchor = GenericForeignKey(
        "anchor_content_type",
        "anchor_object_id",
    )
    absolute_url = models.URLField(blank=True)

    # calculated fields
    cf_nr_followups = models.PositiveSmallIntegerField(blank=True, null=True)
    cf_latest_followup_in_hierarchy = models.ForeignKey(
        "forums.Post",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="latest_followup_in_hierarchy_of",
    )

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = [
            "posted_on",
        ]

    def __str__(self):
        return "%s %s: %s" % (
            self.posted_by.first_name,
            self.posted_by.last_name,
            self.subject[:32],
        )

    def get_absolute_url(self):
        if not self.anchor:
            self.anchor = self.get_anchor_forum_or_meeting()
        if not self.absolute_url:
            self.absolute_url = "%s#post%s" % (
                self.anchor.get_absolute_url(),
                self.id,
            )
            self.save()
        return self.absolute_url

    def update_cfs(self):
        self.update_cf_nr_followups()
        self.update_cf_latest_followup_in_hierarchy()
        if self.parent:
            self.parent.update_cfs()

    @property
    def nr_followups(self):
        nr = 0
        for followup in self.followup_posts.all():
            nr += followup.nr_followups
        if self.followup_posts:
            nr += self.followup_posts.all().count()
        return nr

    def update_cf_nr_followups(self):
        self.cf_nr_followups = self.nr_followups
        self.save()

    @property
    def latest_followup(self):
        return self.followup_posts.last()

    def posts_hierarchy_id_list(self):
        id_list = [self.id]
        for post in self.followup_posts.all():
            id_list += post.posts_hierarchy_id_list()
        return id_list

    @property
    def latest_followup_in_hierarchy(self):
        id_list = self.posts_hierarchy_id_list()
        return Post.objects.filter(pk__in=id_list).exclude(pk=self.id).last()

    def update_cf_latest_followup_in_hierarchy(self):
        self.cf_latest_followup_in_hierarchy = self.latest_followup_in_hierarchy
        self.save()

    def get_anchor_forum_or_meeting(self):
        """
        Climb back the hierarchy up to the original Forum.
        If no Forum is found, return None.
        """

        type_forum = ContentType.objects.get_by_natural_key("forums", "forum")
        type_meeting = ContentType.objects.get_by_natural_key("forums", "meeting")
        if (
            self.parent_content_type == type_forum
            or self.parent_content_type == type_meeting
        ):
            return self.parent
        else:
            return self.parent.get_anchor_forum_or_meeting()


class Motion(Post):
    """
    A Motion is a posting to a Forum or Meeting, on which Forum participants
    can vote.
    """

    post = models.OneToOneField(
        "forums.Post", on_delete=models.CASCADE, parent_link=True
    )
    eligible_for_voting = models.ManyToManyField(
        "auth.User", blank=True, related_name="eligible_to_vote_on_motion"
    )
    in_agreement = models.ManyToManyField(
        "auth.User", blank=True, related_name="agree_on_motion"
    )
    in_doubt = models.ManyToManyField(
        "auth.User", blank=True, related_name="doubt_on_motion"
    )
    in_disagreement = models.ManyToManyField(
        "auth.User", blank=True, related_name="disagree_with_motion"
    )
    in_abstain = models.ManyToManyField(
        "auth.User", blank=True, related_name="abstain_with_motion"
    )
    voting_deadline = models.DateField()
    accepted = models.BooleanField(null=True)

    objects = models.Manager()
