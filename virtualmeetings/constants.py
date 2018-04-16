__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


MOTION_AMENDMENTS = 'ByLawAmend'
MOTION_WORKFLOW = 'Workflow'
MOTION_GENERAL = 'General'
MOTION_CATEGORIES = (
    (MOTION_AMENDMENTS, 'Amendments to by-laws'),
    (MOTION_WORKFLOW, 'Editorial workflow improvements'),
    (MOTION_GENERAL, 'General'),
)
motion_categories_dict = dict(MOTION_CATEGORIES)
