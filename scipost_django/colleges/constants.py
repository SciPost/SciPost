__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


POTENTIAL_FELLOWSHIP_IDENTIFIED = "identified"
POTENTIAL_FELLOWSHIP_NOMINATED = "nominated"
POTENTIAL_FELLOWSHIP_ELECTION_VOTE_ONGOING = "electionvoteongoing"
POTENTIAL_FELLOWSHIP_ELECTED = "elected"
POTENTIAL_FELLOWSHIP_NOT_ELECTED = "notelected"
POTENTIAL_FELLOWSHIP_INVITED = "invited"
POTENTIAL_FELLOWSHIP_REINVITED = "reinvited"
POTENTIAL_FELLOWSHIP_MULTIPLY_REINVITED = "multiplyreinvited"
POTENTIAL_FELLOWSHIP_DECLINED = "declined"
POTENTIAL_FELLOWSHIP_UNRESPONSIVE = "unresponsive"
POTENTIAL_FELLOWSHIP_RETIRED = "retired"
POTENTIAL_FELLOWSHIP_DECEASED = "deceased"
POTENTIAL_FELLOWSHIP_INTERESTED = "interested"
POTENTIAL_FELLOWSHIP_REGISTERED = "registered"
POTENTIAL_FELLOWSHIP_ACTIVE_IN_COLLEGE = "activeincollege"
POTENTIAL_FELLOWSHIP_SCIPOST_EMERITUS = "emeritus"

POTENTIAL_FELLOWSHIP_STATUSES = (
    (POTENTIAL_FELLOWSHIP_IDENTIFIED, "Identified as potential Fellow"),
    (POTENTIAL_FELLOWSHIP_NOMINATED, "Nominated for Fellowship"),
    (POTENTIAL_FELLOWSHIP_ELECTION_VOTE_ONGOING, "Election vote ongoing"),
    (POTENTIAL_FELLOWSHIP_ELECTED, "Elected by the College"),
    (POTENTIAL_FELLOWSHIP_NOT_ELECTED, "Not elected by the College"),
    (POTENTIAL_FELLOWSHIP_INVITED, "Invited to become Fellow"),
    (POTENTIAL_FELLOWSHIP_REINVITED, "Reinvited after initial invitation"),
    (POTENTIAL_FELLOWSHIP_MULTIPLY_REINVITED, "Multiply reinvited"),
    (POTENTIAL_FELLOWSHIP_DECLINED, "Declined the invitation"),
    (POTENTIAL_FELLOWSHIP_UNRESPONSIVE, "Marked as unresponsive"),
    (POTENTIAL_FELLOWSHIP_RETIRED, "Retired"),
    (POTENTIAL_FELLOWSHIP_DECEASED, "Deceased"),
    (POTENTIAL_FELLOWSHIP_INTERESTED, "Marked as interested, Fellowship being set up"),
    (POTENTIAL_FELLOWSHIP_REGISTERED, "Registered as Contributor"),
    (POTENTIAL_FELLOWSHIP_ACTIVE_IN_COLLEGE, "Currently active in a College"),
    (POTENTIAL_FELLOWSHIP_SCIPOST_EMERITUS, "SciPost Emeritus"),
)
potential_fellowship_statuses_dict = dict(POTENTIAL_FELLOWSHIP_STATUSES)


POTENTIAL_FELLOWSHIP_EVENT_DEFINED = "defined"
POTENTIAL_FELLOWSHIP_EVENT_NOMINATED = "nominated"
POTENTIAL_FELLOWSHIP_EVENT_VOTED_ON = "votedon"
POTENTIAL_FELLOWSHIP_EVENT_ELECTED = "elected"
POTENTIAL_FELLOWSHIP_EVENT_EMAILED = "emailed"
POTENTIAL_FELLOWSHIP_EVENT_RESPONDED = "responded"
POTENTIAL_FELLOWSHIP_EVENT_STATUSUPDATED = "statusupdated"
POTENTIAL_FELLOWSHIP_EVENT_COMMENT = "comment"
POTENTIAL_FELLOWSHIP_EVENT_DEACTIVATION = "deactivation"

POTENTIAL_FELLOWSHIP_EVENTS = (
    (POTENTIAL_FELLOWSHIP_EVENT_DEFINED, "Defined in database"),
    (POTENTIAL_FELLOWSHIP_EVENT_NOMINATED, "Nominated"),
    (POTENTIAL_FELLOWSHIP_EVENT_VOTED_ON, "Voted on"),
    (POTENTIAL_FELLOWSHIP_EVENT_ELECTED, "Elected"),
    (POTENTIAL_FELLOWSHIP_EVENT_EMAILED, "Emailed with invitation"),
    (POTENTIAL_FELLOWSHIP_EVENT_RESPONDED, "Response received"),
    (POTENTIAL_FELLOWSHIP_EVENT_STATUSUPDATED, "Status updated"),
    (POTENTIAL_FELLOWSHIP_EVENT_COMMENT, "Comment"),
    (POTENTIAL_FELLOWSHIP_EVENT_DEACTIVATION, "Deactivation: not considered anymore"),
)
