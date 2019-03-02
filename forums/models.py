__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"



from django.db import models
from django.utils import timezone


class Forum(models.Model):
    """
    A Forum is a discussion place for a specified set of Users,
    with access specified on a per-Group or per-User access.
    """
    name = models.CharField(max_length=256)
    slug = models.SlugField(allow_unicode=True)
    accessible_to_group = models.ManyToManyField('auth.Group',
                                                 related_name='group_forums',
                                                 blank=True)
    accessible_to_users = models.ManyToManyField('auth.User',
                                                 related_name='user_forums',
                                                 blank=True)
    publicly_visible = models.BooleanField(default=False)


class Meeting(Forum):
    """
    A Meeting is like a Forum, but with a fixed time span.
    """
    date_from = models.DateField()
    date_until = models.DateField()
    preamble = models.TextField()
    minutes = models.TextField(blank=True, null=True)


class Thread(models.Model):
    """
    A Thread is a container for Posts.
    """
    theme = models.CharField(max_length=256)
    slug = models.SlugField()
    forum = models.ForeignKey('forums.Forum')


class Post(models.Model):
    """
    A comment, feedback, question, ... pertaining to a Thread
    """
    posted_by = models.ForeignKey('auth.User')
    posted_on = models.DateTimeField(default=timezone.now)
    text = models.TextField()
