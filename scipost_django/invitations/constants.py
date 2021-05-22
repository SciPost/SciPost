__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


STATUS_DRAFT, STATUS_SENT, STATUS_SENT_AND_EDITED = ('draft', 'sent', 'edited')
STATUS_DECLINED, STATUS_REGISTERED = ('declined', 'register')
REGISTATION_INVITATION_STATUSES = (
    (STATUS_DRAFT, 'Draft'),
    (STATUS_SENT, 'Sent'),
    (STATUS_SENT_AND_EDITED, 'Sent and edited'),
    (STATUS_DECLINED, 'Declined'),
    (STATUS_REGISTERED, 'Registered'),
)


INVITATION_FORMAL, INVITATION_PERSONAL = ('F', 'P')
INVITATION_STYLE = (
    (INVITATION_FORMAL, 'Formal'),
    (INVITATION_PERSONAL, 'Personal'),
)


INVITATION_EDITORIAL_FELLOW, INVITATION_CONTRIBUTOR, INVITATION_REFEREEING = ('F', 'C', 'R')
INVITATION_TYPE = (
    (INVITATION_EDITORIAL_FELLOW, 'Editorial Fellow'),
    (INVITATION_CONTRIBUTOR, 'Contributor'),
    (INVITATION_REFEREEING, 'Refereeing'),
)
