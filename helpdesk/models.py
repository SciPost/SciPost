__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils import timezone

from .constants import (
    TICKET_PRIORITIES, TICKET_PRIORITY_URGENT, TICKET_PRIORITY_HIGH, TICKET_PRIORITY_MEDIUM,
    TICKET_STATUSES, TICKET_STATUS_UNASSIGNED, TICKET_STATUS_ASSIGNED,
    TICKET_STATUS_PICKEDUP, TICKET_STATUS_PASSED_ON,
    TICKET_STATUS_AWAITING_RESPONSE_ASSIGNEE, TICKET_STATUS_AWAITING_RESPONSE_USER,
    TICKET_STATUS_RESOLVED, TICKET_STATUS_CLOSED,
    TICKET_FOLLOWUP_ACTION_TYPES)
from .managers import QueueQuerySet, TicketQuerySet


class Queue(models.Model):
    """
    A Queue is a container for a category of Tickets.

    Each Ticket has a ForeignKey relationship to a specific Queue.
    A Queue is managed by a specific Group specific by `managing_group`,
    and can be responsed to by users in a set of groups defined by the
    `response_groups` field.

    A Queue is visible only to users in managing or response groups,
    and is thus admin/internal only.

    Permissions are handled at object level using `django_guardian`.
    """
    name = models.CharField(max_length=64)
    slug = models.SlugField(allow_unicode=True, unique=True)
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
            ('can_manage_queue', 'Can manage Queue'),
            ('can_handle_queue', 'Can handle Queue'),
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

    @property
    def nr_awaiting_handling(self):
        return self.tickets.awaiting_handling().count()

    @property
    def nr_in_handling(self):
        return self.tickets.in_handling().count()

    @property
    def nr_handled(self):
        return self.tickets.handled().count()



class Ticket(models.Model):
    """
    User-created ticket, representing a query or request for assistance.

    Each ticket lives in a Queue.
    """
    queue = models.ForeignKey('helpdesk.Queue', on_delete=models.CASCADE,
                              related_name='tickets',
                              help_text=('Don\'t worry and just choose the one that '
                                         'seems most appropriate for your issue'))
    title = models.CharField(max_length=64, default='')
    description = models.TextField(
        help_text=(
            'You can use ReStructuredText, see a '
            '<a href="https://devguide.python.org/documenting/#restructuredtext-primer" '
            'target="_blank">primer on python.org</a>')
        )
    publicly_visible = models.BooleanField(
        default=False,
        help_text=('Do you agree with this Ticket being made publicly visible '
                   '(and appearing, anonymized, in our public Knowledge Base)?'))
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
        permissions = [
            ('can_view_ticket', 'Can view Ticket'),
        ]

    def __str__(self):
        return '%s-%s: %s' % (self.queue.slug, self.pk, self.title)

    def get_absolute_url(self):
        return reverse('helpdesk:ticket_detail', kwargs={'pk': self.id})

    def latest_followup(self):
        return self.followups.order_by('timestamp').last()

    @property
    def latest_activity(self):
        try:
            return self.latest_followup().timestamp
        except AttributeError:
            return self.defined_on

    @property
    def unassigned(self):
        return self.status == TICKET_STATUS_UNASSIGNED

    @property
    def awaiting_handling(self):
        return self.status in [TICKET_STATUS_ASSIGNED, TICKET_STATUS_PASSED_ON]

    @property
    def in_handling(self):
        return self.status in [TICKET_STATUS_PICKEDUP,
                               TICKET_STATUS_AWAITING_RESPONSE_ASSIGNEE,
                               TICKET_STATUS_AWAITING_RESPONSE_USER]

    @property
    def handled(self):
        return self.status in [TICKET_STATUS_RESOLVED, TICKET_STATUS_CLOSED]

    @property
    def open(self):
        """Return True if the Ticket hasn't been resolved or closed."""
        return self.status not in [TICKET_STATUS_RESOLVED, TICKET_STATUS_CLOSED]

    @property
    def priority_icons(self):
        if self.priority == TICKET_PRIORITY_URGENT:
            return ('<i class="fa fa-lg fa-thermometer-full"></i> '
                    '<i class="fa fa-exclamation"></i><i class="fa fa-exclamation"></i>'
                    '<i class="fa fa-exclamation"></i>')
        elif self.priority == TICKET_PRIORITY_HIGH:
            return ('<i class="fa fa-lg fa-thermometer-three-quarters"></i> '
                    '<i class="fa fa-exclamation"></i><i class="fa fa-exclamation"></i>')
        elif self.priority == TICKET_PRIORITY_MEDIUM:
            return ('<i class="fa fa-lg fa-thermometer-half"></i> '
                    '<i class="fa fa-exclamation"></i>')
        else:
            return '<i class="fa fa-lg fa-thermometer-quarter"></i>'

    @property
    def status_classes(self):
        if self.unassigned:
            return {'class': 'danger', 'text': 'white'}
        if self.awaiting_handling:
            return {'class': 'warning', 'text': 'dark'}
        if self.in_handling:
            return {'class': 'success', 'text': 'white'}
        if self.status == TICKET_STATUS_RESOLVED:
            return {'class': 'primary', 'text': 'white'}
        elif self.status == TICKET_STATUS_CLOSED:
            return {'class': 'secondary', 'text': 'dark'}

    @property
    def progress_level(self):
        """For fa box checking: 0 if unassigned, 1 if assigned, 2 if in handling, 3 if handled."""
        if self.unassigned:
            return {'1': '', '2': '', '3': ''}
        elif self.awaiting_handling:
            return {'1': '-check', '2': '', '3': ''}
        elif self.in_handling:
            return {'1': '-check', '2': '-check', '3': ''}
        elif self.handled:
            return {'1': '-check', '2': '-check', '3': '-check'}

class Followup(models.Model):
    """
    Response concerning a Ticket, from either the user or handler.
    """
    ticket = models.ForeignKey('helpdesk.Ticket', on_delete=models.CASCADE,
                               related_name='followups')
    text = models.TextField(blank=True, null=True)
    by = models.ForeignKey('auth.User', on_delete=models.CASCADE,
                           related_name='ticket_followups')
    timestamp = models.DateTimeField()
    action = models.CharField(max_length=32, choices=TICKET_FOLLOWUP_ACTION_TYPES)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return '%s, by %s on %s: %s' % (self.ticket, self.by, self.timestamp,
                                        self.get_action_display())

    def get_absolute_url(self):
        return '%s#%s' % (reverse('helpdesk:ticket_detail', kwargs={'pk': self.ticket.id}), self.id)
