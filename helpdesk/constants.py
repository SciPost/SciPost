__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


TICKET_PRIORITY_URGENT = 'urgent'
TICKET_PRIORITY_HIGH = 'high'
TICKET_PRIORITY_MEDIUM = 'medium'
TICKET_PRIORITY_LOW = 'low'

TICKET_PRIORITIES = [
    (TICKET_PRIORITY_URGENT, 'Urgent (immediate handling needed)'),
    (TICKET_PRIORITY_HIGH, 'High (handle as soon as possible)'),
    (TICKET_PRIORITY_MEDIUM, 'Medium (handle soon)'),
    (TICKET_PRIORITY_LOW, 'Low (handle when available)')
]

TICKET_STATUS_UNASSIGNED = 'unassigned'
TICKET_STATUS_ASSIGNED = 'assigned'
TICKET_STATUS_RESOLVED = 'resolved'
TICKET_STATUS_CLOSED = 'closed'

TICKET_STATUSES = [
    (TICKET_STATUS_UNASSIGNED, 'Unassigned'),
    (TICKET_STATUS_ASSIGNED, 'Assigned'),
    (TICKET_STATUS_RESOLVED, 'Resolved'),
    (TICKET_STATUS_CLOSED, 'Closed')
]
