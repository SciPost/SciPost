__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


NOTIFICATION_REFEREE_DEADLINE = 'referee_task_deadline'
NOTIFICATION_REFEREE_OVERDUE = 'referee_task_overdue'
NOTIFICATION_REPORT_UNFINISHED = 'report_unfinished'

NOTIFICATION_TYPES = (
    (NOTIFICATION_REFEREE_DEADLINE, 'Refereeing Task is approaching its deadline'),
    (NOTIFICATION_REFEREE_OVERDUE, 'Refereeing Task is overdue'),
    (NOTIFICATION_REPORT_UNFINISHED, 'Report is in draft'),
)
