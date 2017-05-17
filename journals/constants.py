# These are DOI's of the Journals, they are used as keys for the choicefield in `models.Journal`!
SCIPOST_JOURNAL_PHYSICS = 'SciPostPhys'
SCIPOST_JOURNAL_PHYSICS_SELECT = 'SciPostPhysSel'
SCIPOST_JOURNAL_PHYSICS_LECTURE_NOTES = 'SciPostPhysLectNotes'
SCIPOST_JOURNAL_PHYSICS_PROC = 'SciPostPhysProc'

# Journal open for submission
SCIPOST_JOURNALS_SUBMIT = (
    (SCIPOST_JOURNAL_PHYSICS, 'SciPost Physics'),
    (SCIPOST_JOURNAL_PHYSICS_LECTURE_NOTES, 'SciPost Physics Lecture Notes')
)

# Journal closed for submission
SCIPOST_JOURNALS_NO_SUBMIT = (
    (SCIPOST_JOURNAL_PHYSICS_SELECT, 'SciPost Physics Select'),
    (SCIPOST_JOURNAL_PHYSICS_PROC, 'SciPost Physics Proceedings'),
)

# All allowed journals
SCIPOST_JOURNALS = SCIPOST_JOURNALS_SUBMIT + SCIPOST_JOURNALS_NO_SUBMIT

REGEX_CHOICES = '|'.join([
    SCIPOST_JOURNAL_PHYSICS_PROC,
    SCIPOST_JOURNAL_PHYSICS_SELECT,
    SCIPOST_JOURNAL_PHYSICS_LECTURE_NOTES,
    SCIPOST_JOURNAL_PHYSICS
])


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

PRODUCTION_STREAM_STATUS = (
    ('ongoing', 'Ongoing'),
    ('completed', 'Completed'),
)

PRODUCTION_EVENTS = (
    ('assigned_to_supervisor', 'Assigned to Supervisor'),
    ('officer_tasked_with_proof_production', 'Officer tasked with proofs production'),
    ('proofs_produced', 'Proofs have been produced'),
    ('proofs_sent_to_authors', 'Proofs sent to Authors'),
    ('proofs_returned_by_authors', 'Proofs returned by Authors'),
    ('corrections_implemented', 'Corrections implemented'),
    ('authors_have_accepted_proofs', 'Authors have accepted proofs'),
)
