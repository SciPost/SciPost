__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime


SUBSIDY_TYPE_SPONSORSHIPAGREEMENT = "sponsorshipagreement"
SUBSIDY_TYPE_INCIDENTALGRANT = "incidentalgrant"
SUBSIDY_TYPE_DEVELOPMENTGRANT = "developmentgrant"
SUBSIDY_TYPE_COLLABORATION = "collaborationagreement"
SUBSIDY_TYPE_COORDINATION_SUPPORT_ACTION = "coordinationsupportaction"
SUBSIDY_TYPE_DONATION = "donation"


SUBSIDY_TYPES = (
    (SUBSIDY_TYPE_SPONSORSHIPAGREEMENT, "Sponsorship Agreement"),
    (SUBSIDY_TYPE_INCIDENTALGRANT, "Incidental Grant"),
    (SUBSIDY_TYPE_DEVELOPMENTGRANT, "Development Grant"),
    (SUBSIDY_TYPE_COLLABORATION, "Collaboration Agreement"),
    (SUBSIDY_TYPE_COORDINATION_SUPPORT_ACTION, "Coordination and Support Action"),
    (SUBSIDY_TYPE_DONATION, "Donation"),
)


SUBSIDY_PROMISED = "promised"
SUBSIDY_INVOICED = "invoiced"
SUBSIDY_RECEIVED = "received"
SUBSIDY_WITHDRAWN = "withdrawn"
SUBSIDY_UPTODATE = "uptodate"

SUBSIDY_STATUS = (
    (SUBSIDY_PROMISED, "Promised"),
    (SUBSIDY_INVOICED, "Invoiced"),
    (SUBSIDY_RECEIVED, "Received"),
    (SUBSIDY_WITHDRAWN, "Withdrawn"),
    (SUBSIDY_UPTODATE, "Up to date"),
)
