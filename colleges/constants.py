__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


POTENTIAL_FELLOWSHIP_IDENTIFIED = 'identified'
POTENTIAL_FELLOWSHIP_INVITED = 'invited'
POTENTIAL_FELLOWSHIP_REINVITED = 'reinvited'
POTENTIAL_FELLOWSHIP_MULTIPLY_REINVITED = 'multiplyreinvited'
POTENTIAL_FELLOWSHIP_DECLINED = 'declined'
POTENTIAL_FELLOWSHIP_UNRESPONSIVE = 'unresponsive'
POTENTIAL_FELLOWSHIP_RETIRED = 'retired'
POTENTIAL_FELLOWSHIP_DECEASED = 'deceased'
POTENTIAL_FELLOWSHIP_INTERESTED = 'interested'
POTENTIAL_FELLOWSHIP_REGISTERED = 'registered'
POTENTIAL_FELLOWSHIP_ACTIVE_IN_COLLEGE = 'activeincollege'
POTENTIAL_FELLOWSHIP_SCIPOST_EMERITUS = 'emeritus'

POTENTIAL_FELLOWSHIP_STATUSES = (
    (POTENTIAL_FELLOWSHIP_IDENTIFIED, 'Identified as potential Fellow'),
    (POTENTIAL_FELLOWSHIP_INVITED, 'Invited to become Fellow'),
    (POTENTIAL_FELLOWSHIP_REINVITED, 'Reinvited after initial invitation'),
    (POTENTIAL_FELLOWSHIP_MULTIPLY_REINVITED, 'Multiply reinvited'),
    (POTENTIAL_FELLOWSHIP_DECLINED, 'Declined the invitation'),
    (POTENTIAL_FELLOWSHIP_UNRESPONSIVE, 'Marked as unresponsive'),
    (POTENTIAL_FELLOWSHIP_RETIRED, 'Retired'),
    (POTENTIAL_FELLOWSHIP_DECEASED, 'Deceased'),
    (POTENTIAL_FELLOWSHIP_INTERESTED, 'Marked as interested, Fellowship being set up'),
    (POTENTIAL_FELLOWSHIP_REGISTERED, 'Registered as Contributor'),
    (POTENTIAL_FELLOWSHIP_ACTIVE_IN_COLLEGE, 'Currently active in a College'),
    (POTENTIAL_FELLOWSHIP_SCIPOST_EMERITUS, 'SciPost Emeritus'),
)
potential_fellowship_statuses_dict = dict(POTENTIAL_FELLOWSHIP_STATUSES)


POTENTIAL_FELLOWSHIP_EVENT_DEFINED = 'defined'
POTENTIAL_FELLOWSHIP_EVENT_EMAILED = 'emailed'
POTENTIAL_FELLOWSHIP_EVENT_RESPONDED = 'responded'
POTENTIAL_FELLOWSHIP_EVENT_STATUSUPDATED = 'statusupdated'
POTENTIAL_FELLOWSHIP_EVENT_COMMENT = 'comment'
POTENTIAL_FELLOWSHIP_EVENT_DEACTIVATION = 'deactivation'

POTENTIAL_FELLOWSHIP_EVENTS = (
    (POTENTIAL_FELLOWSHIP_EVENT_DEFINED, 'Defined in database'),
    (POTENTIAL_FELLOWSHIP_EVENT_EMAILED, 'Emailed with invitation'),
    (POTENTIAL_FELLOWSHIP_EVENT_RESPONDED, 'Response received'),
    (POTENTIAL_FELLOWSHIP_EVENT_STATUSUPDATED, 'Status updated'),
    (POTENTIAL_FELLOWSHIP_EVENT_COMMENT, 'Comment'),
    (POTENTIAL_FELLOWSHIP_EVENT_DEACTIVATION, 'Deactivation: not considered anymore'),
)


# TO BE DEPRECATED:
PROSPECTIVE_FELLOW_IDENTIFIED = 'identified'
PROSPECTIVE_FELLOW_INVITED = 'invited'
PROSPECTIVE_FELLOW_REINVITED = 'reinvited'
PROSPECTIVE_FELLOW_MULTIPLY_REINVITED = 'multiplyreinvited'
PROSPECTIVE_FELLOW_DECLINED = 'declined'
PROSPECTIVE_FELLOW_UNRESPONSIVE = 'unresponsive'
PROSPECTIVE_FELLOW_RETIRED = 'retired'
PROSPECTIVE_FELLOW_DECEASED = 'deceased'
PROSPECTIVE_FELLOW_INTERESTED = 'interested'
PROSPECTIVE_FELLOW_REGISTERED = 'registered'
PROSPECTIVE_FELLOW_ACTIVE_IN_COLLEGE = 'activeincollege'
PROSPECTIVE_FELLOW_SCIPOST_EMERITUS = 'emeritus'

PROSPECTIVE_FELLOW_STATUSES = (
    (PROSPECTIVE_FELLOW_IDENTIFIED, 'Identified as potential Fellow'),
    (PROSPECTIVE_FELLOW_INVITED, 'Invited to become Fellow'),
    (PROSPECTIVE_FELLOW_REINVITED, 'Reinvited after initial invitation'),
    (PROSPECTIVE_FELLOW_MULTIPLY_REINVITED, 'Multiply reinvited'),
    (PROSPECTIVE_FELLOW_DECLINED, 'Declined the invitation'),
    (PROSPECTIVE_FELLOW_UNRESPONSIVE, 'Marked as unresponsive'),
    (PROSPECTIVE_FELLOW_RETIRED, 'Retired'),
    (PROSPECTIVE_FELLOW_DECEASED, 'Deceased'),
    (PROSPECTIVE_FELLOW_INTERESTED, 'Marked as interested, Fellowship being set up'),
    (PROSPECTIVE_FELLOW_REGISTERED, 'Registered as Contributor'),
    (PROSPECTIVE_FELLOW_ACTIVE_IN_COLLEGE, 'Currently active in a College'),
    (PROSPECTIVE_FELLOW_SCIPOST_EMERITUS, 'SciPost Emeritus'),
)
prospective_Fellow_statuses_dict = dict(PROSPECTIVE_FELLOW_STATUSES)


PROSPECTIVE_FELLOW_EVENT_DEFINED = 'defined'
PROSPECTIVE_FELLOW_EVENT_EMAILED = 'emailed'
PROSPECTIVE_FELLOW_EVENT_RESPONDED = 'responded'
PROSPECTIVE_FELLOW_EVENT_STATUSUPDATED = 'statusupdated'
PROSPECTIVE_FELLOW_EVENT_COMMENT = 'comment'
PROSPECTIVE_FELLOW_EVENT_DEACTIVATION = 'deactivation'

PROSPECTIVE_FELLOW_EVENTS = (
    (PROSPECTIVE_FELLOW_EVENT_DEFINED, 'Defined in database'),
    (PROSPECTIVE_FELLOW_EVENT_EMAILED, 'Emailed with invitation'),
    (PROSPECTIVE_FELLOW_EVENT_RESPONDED, 'Response received'),
    (PROSPECTIVE_FELLOW_EVENT_STATUSUPDATED, 'Status updated'),
    (PROSPECTIVE_FELLOW_EVENT_COMMENT, 'Comment'),
    (PROSPECTIVE_FELLOW_EVENT_DEACTIVATION, 'Deactivation: not considered anymore'),
)
