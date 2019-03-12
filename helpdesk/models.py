__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils import timezone

from .constants import TICKET_PRIORITIES, TICKET_STATUSES
from .managers import QueueQuerySet, TicketQuerySet


class Queue(models.Model):
    """
    A Queue is essentially a container for a category of Tickets.

    Each Ticket falls under one specific Queue.
    A Queue is managed by a specific Group.
    """
    name = models.CharField(max_length=64)
    slug = models.SlugField(allow_unicode=True)
    description = models.TextField()
    managing_group = models.ForeignKey('auth.Group', on_delete=models.CASCADE,
                                       related_name='managed_queues')
    response_groups = models.ManyToManyField('auth.Group')
    parent_queue = models.ForeignKey('helpdesk.Queue', on_delete=models.CASCADE,
                                     blank=True, null=True, related_name='sub_queues')

    objects = QueueQuerySet.as_manager()

    class Meta:
        ordering = ['name',]
        permissions = [
            ('can_view_queue', 'Can view Queue'),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('helpdesk:queue_detail', kwargs={'slug': self.slug})

    @property
    def nr_unassigned(self):
        return self.tickets.unassigned().count()

    @property
    def nr_assigned(self):
        return self.tickets.assigned().count()

    @property
    def nr_resolved(self):
        return self.tickets.resolved().count()

    @property
    def nr_closed(self):
        return self.tickets.closed().count()


class Ticket(models.Model):
    """
    User-created ticket, representing a query or request for assistance.

    Each ticket lives in a Queue.
    """
    queue = models.ForeignKey('helpdesk.Queue', on_delete=models.CASCADE,
                              related_name='tickets')
    description = models.TextField(
        help_text=(
            'You can use ReStructuredText, see a '
            '<a href="https://devguide.python.org/documenting/#restructuredtext-primer" '
            'target="_blank">primer on python.org</a>')
        )
    publicly_visible = models.BooleanField(
        default=False,
        help_text=('Do you agree with this Ticket being made publicly visible '
                   '(and appearing in our public Knowledge Base)?'))
    defined_on = models.DateTimeField(default=timezone.now)
    defined_by = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    priority = models.CharField(max_length=32, choices=TICKET_PRIORITIES)
    deadline = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=32, choices=TICKET_STATUSES)
    assigned_to = models.ForeignKey('auth.User', on_delete=models.SET_NULL,
                                    blank=True, null=True, related_name='assigned_tickets')
    concerning_object_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                               blank=True, null=True)
    concerning_object_id = models.PositiveIntegerField(blank=True, null=True)
    concerning_object = GenericForeignKey('concerning_object_type', 'concerning_object_id')

    objects = TicketQuerySet.as_manager()

    class Meta:
        ordering = ['queue', 'priority']

    def __str__(self):
        return '%s - %s' % (self.queue, self.pk)
