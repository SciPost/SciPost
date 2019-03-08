__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from docutils.core import publish_parts, publish_string

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone

from .managers import ForumQuerySet


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
    publicly_visible = models.BooleanField(default=False)
    moderators = models.ManyToManyField('auth.User', related_name='moderated_forums')

    parent_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                            blank=True, null=True)
    parent_object_id = models.PositiveIntegerField(blank=True, null=True)
    parent = GenericForeignKey('parent_content_type', 'parent_object_id')

    child_forums = GenericRelation('forums.Forum',
                                   content_type_field='parent_content_type',
                                   object_id_field='parent_object_id',
                                   related_query_name='parent_forums')
    posts = GenericRelation('forums.Post',
                            content_type_field='parent_content_type',
                            object_id_field='parent_object_id',
                            related_query_name='parent_forums')

    objects = ForumQuerySet.as_manager()

    class Meta:
        ordering = ['name',]
        permissions = [
            ('can_view_forum', 'Can view Forum'),
            ('can_post_to_forum', 'Can add Post to Forum'),
        ]

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('forums:forum_detail', kwargs={'slug': self.slug})

    @property
    def nr_posts(self):
        """Recursively counts the number of posts in this Forum."""
        nr = 0
        for post in self.posts.all():
            nr += post.nr_followups
        if self.posts.all():
            nr += self.posts.all().count()
        return nr

    def posts_hierarchy_id_list(self):
        id_list = []
        for post in self.posts.all():
            id_list += post.posts_hierarchy_id_list()
        return id_list

    @property
    def latest_post(self):
        id_list = self.posts_hierarchy_id_list()
        print ('forum post id_list: %s' % id_list)
        try:
            return Post.objects.filter(id__in=id_list).order_by('-posted_on').first()
        except:
            return None


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

    The text field can contain ReStructuredText markup, formatted in templates
    through the django-docutils required app.
    """
    posted_by = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    posted_on = models.DateTimeField(default=timezone.now)
    needs_vetting = models.BooleanField(default=True)
    vetted_by = models.ForeignKey('auth.User', related_name='vetted_posts',
                                  blank=True, null=True, on_delete=models.PROTECT)
    parent_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    parent_object_id = models.PositiveIntegerField()
    parent = GenericForeignKey('parent_content_type', 'parent_object_id')
    followup_posts = GenericRelation('forums.Post',
                                     content_type_field='parent_content_type',
                                     object_id_field='parent_object_id',
                                     related_query_name='parent_posts')
    subject = models.CharField(max_length=256)
    text = models.TextField(help_text='You can use ReStructuredText, see a <a href="https://devguide.python.org/documenting/#restructuredtext-primer" target="_blank">primer on python.org</a>')

    class Meta:
        ordering = ['posted_on',]

    def __str__(self):
        return '%s: %s' % (self.posted_by, self.subject[:32])

    def get_absolute_url(self):
        return '%s#post%s' % (self.get_forum().get_absolute_url(), self.id)

    @property
    def nr_followups(self):
        nr = 0
        for followup in self.followup_posts.all():
            nr += followup.nr_followups
        if self.followup_posts:
            nr += self.followup_posts.all().count()
        return nr

    def posts_hierarchy_id_list(self):
        id_list = [self.id]
        for post in self.followup_posts.all():
            id_list += post.posts_hierarchy_id_list()
        print ('post %s id_list: %s' % (self.id, id_list))
        return id_list

    def get_forum(self):
        """
        Climb back the hierarchy up to the original Forum.
        If no Forum is found, return None.
        """
        type_forum = ContentType.objects.get_by_natural_key('forums', 'forum')
        if self.parent_content_type == type_forum:
            return self.parent
        else:
            return self.parent.get_forum()
