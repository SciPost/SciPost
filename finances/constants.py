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


SUBSIDY_DURATION = (
    (datetime.timedelta(days=365), '1 year'),
    (datetime.timedelta(days=730), '2 years'),
    (datetime.timedelta(days=1095), '3 years'),
    (datetime.timedelta(days=1460), '4 years'),
    (datetime.timedelta(days=1825), '5 years'),
    (datetime.timedelta(days=3650), '10 years'),
    (datetime.timedelta(days=36500), 'Indefinite (100 years)'),
)
