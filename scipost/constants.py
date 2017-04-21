import datetime


DISCIPLINE_PHYSICS = 'physics'
DISCIPLINE_ASTROPHYSICS = 'astrophysics'
DISCIPLINE_MATH = 'mathematics'
DISCIPLINE_COMPUTERSCIENCE = 'computerscience'
SCIPOST_DISCIPLINES = (
    (DISCIPLINE_PHYSICS, 'Physics'),
    (DISCIPLINE_ASTROPHYSICS, 'Astrophysics'),
    (DISCIPLINE_MATH, 'Mathematics'),
    (DISCIPLINE_COMPUTERSCIENCE, 'Computer Science'),
)

SCIPOST_SUBJECT_AREAS = (
    ('Physics', (
        ('Phys:AE', 'Atomic, Molecular and Optical Physics - Experiment'),
        ('Phys:AT', 'Atomic, Molecular and Optical Physics - Theory'),
        ('Phys:BI', 'Biophysics'),
        ('Phys:CE', 'Condensed Matter Physics - Experiment'),
        ('Phys:CT', 'Condensed Matter Physics - Theory'),
        ('Phys:FD', 'Fluid Dynamics'),
        ('Phys:GR', 'Gravitation, Cosmology and Astroparticle Physics'),
        ('Phys:HE', 'High-Energy Physics - Experiment'),
        ('Phys:HT', 'High-Energy Physics- Theory'),
        ('Phys:HP', 'High-Energy Physics - Phenomenology'),
        ('Phys:MP', 'Mathematical Physics'),
        ('Phys:NE', 'Nuclear Physics - Experiment'),
        ('Phys:NT', 'Nuclear Physics - Theory'),
        ('Phys:QP', 'Quantum Physics'),
        ('Phys:SM', 'Statistical and Soft Matter Physics'),
        )
     ),
    ('Astrophysics', (
        ('Astro:GA', 'Astrophysics of Galaxies'),
        ('Astro:CO', 'Cosmology and Nongalactic Astrophysics'),
        ('Astro:EP', 'Earth and Planetary Astrophysics'),
        ('Astro:HE', 'High Energy Astrophysical Phenomena'),
        ('Astro:IM', 'Instrumentation and Methods for Astrophysics'),
        ('Astro:SR', 'Solar and Stellar Astrophysics'),
        )
     ),
    ('Mathematics', (
        ('Math:AG', 'Algebraic Geometry'),
        ('Math:AT', 'Algebraic Topology'),
        ('Math:AP', 'Analysis of PDEs'),
        ('Math:CT', 'Category Theory'),
        ('Math:CA', 'Classical Analysis and ODEs'),
        ('Math:CO', 'Combinatorics'),
        ('Math:AC', 'Commutative Algebra'),
        ('Math:CV', 'Complex Variables'),
        ('Math:DG', 'Differential Geometry'),
        ('Math:DS', 'Dynamical Systems'),
        ('Math:FA', 'Functional Analysis'),
        ('Math:GM', 'General Mathematics'),
        ('Math:GN', 'General Topology'),
        ('Math:GT', 'Geometric Topology'),
        ('Math:GR', 'Group Theory'),
        ('Math:HO', 'History and Overview'),
        ('Math:IT', 'Information Theory'),
        ('Math:KT', 'K-Theory and Homology'),
        ('Math:LO', 'Logic'),
        ('Math:MP', 'Mathematical Physics'),
        ('Math:MG', 'Metric Geometry'),
        ('Math:NT', 'Number Theory'),
        ('Math:NA', 'Numerical Analysis'),
        ('Math:OA', 'Operator Algebras'),
        ('Math:OC', 'Optimization and Control'),
        ('Math:PR', 'Probability'),
        ('Math:QA', 'Quantum Algebra'),
        ('Math:RT', 'Representation Theory'),
        ('Math:RA', 'Rings and Algebras'),
        ('Math:SP', 'Spectral Theory'),
        ('Math:ST', 'Statistics Theory'),
        ('Math:SG', 'Symplectic Geometry'),
        )
     ),
    ('Computer Science', (
        ('Comp:AI', 'Artificial Intelligence'),
        ('Comp:CC', 'Computational Complexity'),
        ('Comp:CE', 'Computational Engineering, Finance, and Science'),
        ('Comp:CG', 'Computational Geometry'),
        ('Comp:GT', 'Computer Science and Game Theory'),
        ('Comp:CV', 'Computer Vision and Pattern Recognition'),
        ('Comp:CY', 'Computers and Society'),
        ('Comp:CR', 'Cryptography and Security'),
        ('Comp:DS', 'Data Structures and Algorithms'),
        ('Comp:DB', 'Databases'),
        ('Comp:DL', 'Digital Libraries'),
        ('Comp:DM', 'Discrete Mathematics'),
        ('Comp:DC', 'Distributed, Parallel, and Cluster Computing'),
        ('Comp:ET', 'Emerging Technologies'),
        ('Comp:FL', 'Formal Languages and Automata Theory'),
        ('Comp:GL', 'General Literature'),
        ('Comp:GR', 'Graphics'),
        ('Comp:AR', 'Hardware Architecture'),
        ('Comp:HC', 'Human-Computer Interaction'),
        ('Comp:IR', 'Information Retrieval'),
        ('Comp:IT', 'Information Theory'),
        ('Comp:LG', 'Learning'),
        ('Comp:LO', 'Logic in Computer Science'),
        ('Comp:MS', 'Mathematical Software'),
        ('Comp:MA', 'Multiagent Systems'),
        ('Comp:MM', 'Multimedia'),
        ('Comp:NI', 'Networking and Internet Architecture'),
        ('Comp:NE', 'Neural and Evolutionary Computing'),
        ('Comp:NA', 'Numerical Analysis'),
        ('Comp:OS', 'Operating Systems'),
        ('Comp:OH', 'Other Computer Science'),
        ('Comp:PF', 'Performance'),
        ('Comp:PL', 'Programming Languages'),
        ('Comp:RO', 'Robotics'),
        ('Comp:SI', 'Social and Information Networks'),
        ('Comp:SE', 'Software Engineering'),
        ('Comp:SD', 'Sound'),
        ('Comp:SC', 'Symbolic Computation'),
        ('Comp:SY', 'Systems and Control'),
        )
     ),
)
subject_areas_raw_dict = dict(SCIPOST_SUBJECT_AREAS)

# Make dict of the form {'Phys:AT': 'Atomic...', ...}
subject_areas_dict = {}
for k in subject_areas_raw_dict.keys():
    subject_areas_dict.update(dict(subject_areas_raw_dict[k]))

CONTRIBUTOR_NORMAL = 1
CONTRIBUTOR_STATUS = (
    # status determine the type of Contributor:
    # 0: newly registered (unverified; not allowed to submit, comment or vote)
    # 1: contributor has been vetted through
    #
    # Negative status denotes rejected requests or:
    # -1: not a professional scientist (>= PhD student in known university)
    # -2: other account already exists for this person
    # -3: barred from SciPost (abusive behaviour)
    # -4: disabled account (deceased)
    (0, 'newly registered'),
    (CONTRIBUTOR_NORMAL, 'normal user'),
    (-1, 'not a professional scientist'),
    (-2, 'other account already exists'),
    (-3, 'barred from SciPost'),
    (-4, 'account disabled'),
    )

TITLE_CHOICES = (
    ('PR', 'Prof.'),
    ('DR', 'Dr'),
    ('MR', 'Mr'),
    ('MRS', 'Mrs'),
)

INVITATION_EDITORIAL_FELLOW = 'F'
INVITATION_CONTRIBUTOR = 'C'
INVITATION_REFEREEING = 'R'
INVITATION_CITED_SUBMISSION = 'ci'
INVITATION_CITED_PUBLICATION = 'cp'
INVITATION_TYPE = (
    (INVITATION_EDITORIAL_FELLOW, 'Editorial Fellow'),
    (INVITATION_CONTRIBUTOR, 'Contributor'),
    (INVITATION_REFEREEING, 'Refereeing'),
    (INVITATION_CITED_SUBMISSION, 'cited in submission'),
    (INVITATION_CITED_PUBLICATION, 'cited in publication'),
)

INVITATION_FORMAL = 'F'
INVITATION_PERSONAL = 'P'
INVITATION_STYLE = (
    (INVITATION_FORMAL, 'formal'),
    (INVITATION_PERSONAL, 'personal'),
)

AUTHORSHIP_CLAIM_ACCEPTED = 1
AUTHORSHIP_CLAIM_PENDING = 0
AUTHORSHIP_CLAIM_REJECTED = -1
AUTHORSHIP_CLAIM_STATUS = (
    (AUTHORSHIP_CLAIM_ACCEPTED, 'accepted'),
    (AUTHORSHIP_CLAIM_PENDING, 'not yet vetted (pending)'),
    (AUTHORSHIP_CLAIM_REJECTED, 'rejected'),
)

SCIPOST_FROM_ADDRESSES = (
    ('Admin', 'SciPost Admin <admin@scipost.org>'),
    ('J.-S. Caux', 'J.-S. Caux <jscaux@scipost.org>'),
    ('J. van Wezel', 'J. van Wezel <vanwezel@scipost.org>'),
)
SciPost_from_addresses_dict = dict(SCIPOST_FROM_ADDRESSES)

#
# Supporting partner models
#
PARTNER_TYPES = (
    ('Int. Fund. Agency', 'International Funding Agency'),
    ('Nat. Fund. Agency', 'National Funding Agency'),
    ('Nat. Library', 'National Library'),
    ('Univ. Library', 'University Library'),
    ('Res. Library', 'Research Library'),
    ('Consortium', 'Consortium'),
    ('Foundation', 'Foundation'),
    ('Individual', 'Individual'),
)

PARTNER_STATUS = (
    ('Prospective', 'Prospective'),
    ('Active', 'Active'),
    ('Inactive', 'Inactive'),
)


SPB_MEMBERSHIP_AGREEMENT_STATUS = (
    ('Submitted', 'Request submitted by Partner'),
    ('Pending', 'Sent to Partner, response pending'),
    ('Signed', 'Signed by Partner'),
    ('Honoured', 'Honoured: payment of Partner received'),
)

SPB_MEMBERSHIP_DURATION = (
    (datetime.timedelta(days=365), '1 year'),
    (datetime.timedelta(days=730), '2 years'),
    (datetime.timedelta(days=1095), '3 years'),
    (datetime.timedelta(days=1460), '4 years'),
    (datetime.timedelta(days=1825), '5 years'),
)
