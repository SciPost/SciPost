__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


DIFFERENT_PEOPLE = 'DifferentPeople'
MULTIPLE_ALLOWED = 'MultipleAllowed'

PROFILE_NON_DUPLICATE_REASONS = (
    (DIFFERENT_PEOPLE, 'These are different people'),
    (MULTIPLE_ALLOWED, 'Multiple Profiles allowed for this person'),
)


AFFILIATION_CATEGORY_EMPLOYED_PROF_FULL = 'employed_prof_full'
AFFILIATION_CATEGORY_EMPLOYED_PROF_ASSOCIATE = 'employed_prof_associate'
AFFILIATION_CATEGORY_EMPLOYED_PROF_ASSISTANT = 'employed_prof_assistant'
AFFILIATION_CATEGORY_EMPLOYED_PROF_EMERITUS = 'employed_prof_emeritus'
AFFILIATION_CATEGORY_EMPLOYED_PERMANENT_STAFF = 'employed_permanent_staff'
AFFILIATION_CATEGORY_EMPLOYED_FIXED_TERM_STAFF = 'employed_fixed_term_staff'
AFFILIATION_CATEGORY_EMPLOYED_TENURE_TRACK = 'employed_tenure_track'
AFFILIATION_CATEGORY_EMPLOYED_POSTDOC = 'employed_postdoc'
AFFILIATION_CATEGORY_EMPLOYED_PhD = 'employed_phd'
AFFILIATION_CATEGORY_ASSOCIATE_SCIENTIST = 'associate_scientist'
AFFILIATION_CATEGORY_CONSULTANT = 'consultant'
AFFILIATION_CATEGORY_VISITOR = 'visitor'

AFFILIATION_CATEGORIES = (
    (AFFILIATION_CATEGORY_EMPLOYED_PROF_FULL, 'Full Professor'),
    (AFFILIATION_CATEGORY_EMPLOYED_PROF_ASSOCIATE, 'Associate Professor'),
    (AFFILIATION_CATEGORY_EMPLOYED_PROF_ASSISTANT, 'Assistant Professor'),
    (AFFILIATION_CATEGORY_EMPLOYED_PROF_EMERITUS, 'Emeritus Professor'),
    (AFFILIATION_CATEGORY_EMPLOYED_PERMANENT_STAFF, 'Permanent Staff'),
    (AFFILIATION_CATEGORY_EMPLOYED_FIXED_TERM_STAFF, 'Fixed Term Staff'),
    (AFFILIATION_CATEGORY_EMPLOYED_TENURE_TRACK, 'Tenure Tracker'),
    (AFFILIATION_CATEGORY_EMPLOYED_POSTDOC, 'Postdoctoral Researcher'),
    (AFFILIATION_CATEGORY_EMPLOYED_PhD, 'PhD candidate'),
    (AFFILIATION_CATEGORY_ASSOCIATE_SCIENTIST, 'Associate Scientist'),
    (AFFILIATION_CATEGORY_CONSULTANT, 'Consultant'),
    (AFFILIATION_CATEGORY_VISITOR, 'Visotor'),
)
