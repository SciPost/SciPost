SCIPOST_JOURNAL_PHYSICS_SELECT = 'SciPost Physics Select'
SCIPOST_JOURNAL_PHYSICS = 'SciPost Physics'
SCIPOST_JOURNAL_LECTURE_NOTES = 'SciPost Physics Lecture Notes'
SCIPOST_JOURNALS = (
    (SCIPOST_JOURNAL_PHYSICS_SELECT, 'SciPost Physics Select'),
    (SCIPOST_JOURNAL_PHYSICS, 'SciPost Physics'),
    (SCIPOST_JOURNAL_LECTURE_NOTES, 'SciPost Physics Lecture Notes'),
)

# Same as SCIPOST_JOURNALS, but SciPost Select deactivated
SCIPOST_JOURNALS_SUBMIT = (
    (SCIPOST_JOURNAL_PHYSICS, 'SciPost Physics'),
    (SCIPOST_JOURNAL_LECTURE_NOTES, 'SciPost Physics Lecture Notes'),
)

SCIPOST_JOURNALS_DOMAINS = (
    ('E', 'Experimental'),
    ('T', 'Theoretical'),
    ('C', 'Computational'),
    ('ET', 'Exp. & Theor.'),
    ('EC', 'Exp. & Comp.'),
    ('TC', 'Theor. & Comp.'),
    ('ETC', 'Exp., Theor. & Comp.'),
)

SCIPOST_JOURNALS_SPECIALIZATIONS = (
    ('A', 'Atomic, Molecular and Optical Physics'),
    ('B', 'Biophysics'),
    ('C', 'Condensed Matter Physics'),
    ('F', 'Fluid Dynamics'),
    ('G', 'Gravitation, Cosmology and Astroparticle Physics'),
    ('H', 'High-Energy Physics'),
    ('M', 'Mathematical Physics'),
    ('N', 'Nuclear Physics'),
    ('Q', 'Quantum Statistical Mechanics'),
    ('S', 'Statistical and Soft Matter Physics'),
)

STATUS_DRAFT = 'draft'
STATUS_PUBLISHED = 'published'
ISSUE_STATUSES = (
    (STATUS_DRAFT, 'Draft'),
    (STATUS_PUBLISHED, 'Published'),
)

JOURNALS_NAME_MAPPING = {
    'SciPostPhys': 'SciPost Physics',
    'SciPostPhysProc': 'SciPost Physics Proceedings',
}
