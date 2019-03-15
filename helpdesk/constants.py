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
TICKET_STATUS_PASSED_ON = 'passedon'
TICKET_STATUS_PICKEDUP = 'pickedup'
TICKET_STATUS_AWAITING_RESPONSE_ASSIGNEE = 'awaitingassignee'
TICKET_STATUS_AWAITING_RESPONSE_USER = 'awaitinguser'
TICKET_STATUS_RESOLVED = 'resolved'
TICKET_STATUS_CLOSED = 'closed'

TICKET_STATUSES = [
    (TICKET_STATUS_UNASSIGNED, 'Unassigned, waiting for triage'),
    (TICKET_STATUS_ASSIGNED, 'Assigned, waiting for handler'),
    (TICKET_STATUS_PASSED_ON, 'Passed on to other handler'),
    (TICKET_STATUS_PICKEDUP, 'Picked up by handler'),
    (TICKET_STATUS_AWAITING_RESPONSE_ASSIGNEE, 'Awaiting response from SciPost'),
    (TICKET_STATUS_AWAITING_RESPONSE_USER, 'Awaiting response from user'),
    (TICKET_STATUS_RESOLVED, 'Resolved'),
    (TICKET_STATUS_CLOSED, 'Closed')
]

TICKET_FOLLOWUP_ACTION_UPDATE = 'update'
TICKET_FOLLOWUP_ACTION_ASSIGNMENT = 'assignment'
TICKET_FOLLOWUP_ACTION_REASSIGNMENT = 'reassignment'
TICKET_FOLLOWUP_ACTION_PICKUP = 'pickup'
TICKET_FOLLOWUP_ACTION_RESPONDED_TO_USER = 'respondedtouser'
TICKET_FOLLOWUP_ACTION_USER_RESPONDED = 'userresonponded'
TICKET_FOLLOWUP_ACTION_MARK_RESOLVED = 'markresolved'
TICKET_FOLLOWUP_ACTION_MARK_CLOSED = 'markcloseed'

TICKET_FOLLOWUP_ACTION_TYPES = [
    (TICKET_FOLLOWUP_ACTION_UPDATE, 'Updated'),
    (TICKET_FOLLOWUP_ACTION_ASSIGNMENT, 'Assignment'),
    (TICKET_FOLLOWUP_ACTION_REASSIGNMENT, 'Reassignment'),
    (TICKET_FOLLOWUP_ACTION_PICKUP, 'Pickup by handler'),
    (TICKET_FOLLOWUP_ACTION_RESPONDED_TO_USER, 'Response sent to user'),
    (TICKET_FOLLOWUP_ACTION_USER_RESPONDED, 'User responded'),
    (TICKET_FOLLOWUP_ACTION_MARK_RESOLVED, 'Marked as resolved'),
    (TICKET_FOLLOWUP_ACTION_MARK_CLOSED, 'Mark as closeed'),
]
