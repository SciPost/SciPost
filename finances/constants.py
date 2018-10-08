__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime


SUBSIDY_TYPE_GRANT = 'grant'
SUBSIDY_TYPE_PARTNERAGREEMENT = 'partneragreement'
SUBSIDY_TYPE_COLLABORATION = 'collaborationagreement'

SUBSIDY_TYPES = (
    (SUBSIDY_TYPE_GRANT, 'Grant'),
    (SUBSIDY_TYPE_PARTNERAGREEMENT, 'Partner Agreement'),
    (SUBSIDY_TYPE_COLLABORATION, 'Collaboration Agreement'),
)


SUBSIDY_PROMISED = 'promised'
SUBSIDY_INVOICED = 'invoiced'
SUBSIDY_RECEIVED = 'received'

SUBSIDY_STATUS = (
    (SUBSIDY_PROMISED, 'promised'),
    (SUBSIDY_INVOICED, 'invoiced'),
    (SUBSIDY_RECEIVED, 'received'),
)
