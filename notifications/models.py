from django.db import models
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone

from .constants import NOTIFICATION_TYPES
from .managers import NotificationQuerySet


class FakeActors(models.Model):
    """
    This Model acts as a surrogate person that either is unknown, deceased, fake, etc. etc.
    """
    name = models.CharField(max_length=256)

    def __str__(self):
        return self.name


class Notification(models.Model):
    """
    Action model describing the actor acting out a verb (on an optional
    target).
    Nomenclature based on http://activitystrea.ms/specs/atom/1.0/
    Generalized Format::
        <actor> <verb> <time>
        <actor> <verb> <target> <time>
        <actor> <verb> <action_object> <target> <time>
    Examples::
        <justquick> <reached level 60> <1 minute ago>
        <brosner> <commented on> <pinax/pinax> <2 hours ago>
        <washingtontimes> <started follow> <justquick> <8 minutes ago>
        <mitsuhiko> <closed> <issue 70> on <mitsuhiko/flask> <about 2 hours ago>
    Unicode Representation::
        justquick reached level 60 1 minute ago
        mitsuhiko closed issue 70 on mitsuhiko/flask 3 hours ago
    """
    LEVELS = (('success', 'Success'), ('info', 'Info'), ('warning', 'Warning'), ('error', 'Error'))
    level = models.CharField(choices=LEVELS, default='info', max_length=20)

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, blank=False,
                                  related_name='notifications')
    unread = models.BooleanField(default=True)
    pseudo_unread = models.BooleanField(default=True)  # Used to keep notification-bg "active"

    actor_content_type = models.ForeignKey(ContentType, related_name='notify_actor')
    actor_object_id = models.CharField(max_length=255)
    actor = GenericForeignKey('actor_content_type', 'actor_object_id')

    verb = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    target_content_type = models.ForeignKey(ContentType, related_name='notify_target',
                                            blank=True, null=True)
    target_object_id = models.CharField(max_length=255, blank=True, null=True)
    target = GenericForeignKey('target_content_type', 'target_object_id')

    action_object_content_type = models.ForeignKey(ContentType, blank=True, null=True,
                                                   related_name='notify_action_object')
    action_object_object_id = models.CharField(max_length=255, blank=True, null=True)
    action_object = GenericForeignKey('action_object_content_type', 'action_object_object_id')

    created = models.DateTimeField(auto_now_add=True)

    # This field is for internal use only. It is used to prevent duplicate sending
    # of notifications.
    internal_type = models.CharField(max_length=255, blank=True, choices=NOTIFICATION_TYPES)

    objects = NotificationQuerySet.as_manager()

    class Meta:
        ordering = ('-created', )

    def __str__(self):
        ctx = {
            'actor': self.actor,
            'verb': self.verb,
            'action_object': self.action_object,
            'target': self.target,
            'timesince': self.timesince()
        }
        if self.target:
            if self.action_object:
                return u'%(actor)s %(verb)s %(action_object)s on %(target)s %(timesince)s ago' % ctx
            return u'%(actor)s %(verb)s %(target)s %(timesince)s ago' % ctx
        if self.action_object:
            return u'%(actor)s %(verb)s %(action_object)s %(timesince)s ago' % ctx
        return u'%(actor)s %(verb)s %(timesince)s ago' % ctx

    def get_absolute_url(self):
        return reverse('notifications:forward', args=(self.slug,))

    def timesince(self, now=None):
        """
        Shortcut for the ``django.utils.timesince.timesince`` function of the
        current timestamp.
        """
        from django.utils.timesince import timesince as timesince_
        return timesince_(self.created, now)

    @property
    def slug(self):
        from .utils import id2slug
        return id2slug(self.id)

    def mark_toggle(self):
        if self.pseudo_unread:
            self.unread = False
            self.pseudo_unread = False
        else:
            self.unread = True
            self.pseudo_unread = True
        self.save()

    def mark_as_read(self):
        if self.unread or self.pseudo_unread:
            self.unread = False
            self.pseudo_unread = False
            self.save()

    def mark_as_unread(self):
        if not self.unread or not self.pseudo_unread:
            self.unread = True
            self.pseudo_unread = True
            self.save()
