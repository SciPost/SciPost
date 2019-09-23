__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


DISCIPLINE_MULTI_ALL = 'multidisciplinary'

DISCIPLINE_MULTI_FORMAL = 'multidiscip-formal'
DISCIPLINE_MATHEMATICS = 'mathematics'
DISCIPLINE_COMPUTERSCIENCE = 'computerscience'

DISCIPLINE_MULTI_NATURAL = 'multidiscip-natural'
DISCIPLINE_PHYSICS = 'physics'
DISCIPLINE_ASTRONOMY = 'astronomy'
DISCIPLINE_ASTROPHYSICS = 'astrophysics'
DISCIPLINE_BIOLOGY = 'biology'
DISCIPLINE_CHEMISTRY = 'chemistry'
DISCIPLINE_EARTHSCIENCE = 'earthscience' 'Earth and Environmental Sciences'

DISCIPLINE_ENGINEERING_MULTI = 'multidiscip-eng'
DISCIPLINE_CIVILENGINEERING = 'civileng'
DISCIPLINE_ELECTRICALENGINEERING = 'electricaleng'
DISCIPLINE_MECHANICALENGINEERING = 'mechanicaleng'
DISCIPLINE_CHEMICALENGINEERING = 'chemicaleng'
DISCIPLINE_MATERIALSENGINEERING = 'materialseng'
DISCIPLINE_MEDICALENGINEERING = 'medicaleng'
DISCIPLINE_ENVIRONMENTALENGINEERING = 'environmentaleng'
DISCIPLINE_INDUSTRIALENGINEERING = 'industrialeng'

DISCIPLINE_MEDICAL_MULTI = 'multidiscip-med'
DISCIPLINE_MEDICINE = 'medicine'
DISCIPLINE_CLINICAL = 'clinical' 'Clinical Medicine'
DISCIPLINE_HEALTH = 'health' 'Health Sciences'

DISCIPLINE_AGRICULTURAL_MULTI = 'multidiscip-agri'
DISCIPLINE_AGRICULTURAL = 'agricultural' 'Agriculture, Forestry and Fisheries'
DISCIPLINE_VETERINARY = 'veterinary'

DISCIPLINE_MULTI_SOCIAL = 'multidiscip-social'
DISCIPLINE_ECONOMICS = 'economics'
DISCIPLINE_GEOGRAPHY = 'geography'
DISCIPLINE_LAW = 'law'
DISCIPLINE_MEDIA = 'media'
DISCIPLINE_PEDAGOGY = 'pedagogy'
DISCIPLINE_POLITICALSCIENCE = 'politicalscience'
DISCIPLINE_PSYCHOLOGY = 'psychology'
DISCIPLINE_SOCIOLOGY = 'sociology'

DISCIPLINE_MULTI_HUMANITIES = 'multidiscip-hum'
DISCIPLINE_ART = 'art' 'Art (arts, history or arts, performing arts, music)'
DISCIPLINE_HISTORY = 'history' 'History and Archeology'
DISCIPLINE_LITERATURE = 'literature' 'Language and Literature'
DISCIPLINE_PHILOSOPHY = 'philosophy' 'Philosophy, Ethics and Religion'


# This classification more or less follows the document
# DSTI/EAS/STP/NESTI(2006)19/FINAL from 2007-02-26
# Working Party of National Experts on Science and Technology Indicators
# REVISED FIELD OF SCIENCE AND TECHNOLOGY (FOS) CLASSIFICATION IN THE FRASCATI MANUAL
SCIPOST_DISCIPLINES = (
    ('Multidisciplinary',
     (
         (DISCIPLINE_MULTI_ALL, 'Multidisciplinary (any combination)'),
         # (DISCIPLINE_MULTI_FORMAL, 'Multidisciplinary (within Formal Sciences)'),
         # (DISCIPLINE_MULTI_NATURAL, 'Multidisciplinary (within Natural Sciences)'),
         # (DISCIPLINE_ENGINEERING_MULTI, 'Multidisciplinary (within Engineering and Technology)'),
         # (DISCIPLINE_MEDICAL_MULTI, 'Multidisciplinary (within Medical Sciences)'),
         # (DISCIPLINE_AGRICULTURAL_MULTI, 'Multidisciplinary (within Agricultural Sciences)'),
         # (DISCIPLINE_MULTI_SOCIAL, 'Multidisciplinary (within Social Sciences)'),
         # (DISCIPLINE_MULTI_HUMANITIES, 'Multidisciplinary (within Humanities)'),
     )
    ),
    ('Formal Sciences',
     (
         (DISCIPLINE_MATHEMATICS, 'Mathematics'),
         (DISCIPLINE_COMPUTERSCIENCE, 'Computer Science'),
     )
    ),
    ('Natural Sciences',
     (
         (DISCIPLINE_PHYSICS, 'Physics'),
         (DISCIPLINE_ASTRONOMY, 'Astronomy'),
         (DISCIPLINE_ASTROPHYSICS, 'Astrophysics'),
         (DISCIPLINE_BIOLOGY, 'Biology'),
         (DISCIPLINE_CHEMISTRY, 'Chemistry'),
         (DISCIPLINE_EARTHSCIENCE, 'Earth and Environmental Sciences'),
     )
    ),
    ('Engineering',
     (
         (DISCIPLINE_CIVILENGINEERING, 'Civil Engineering'),
         (DISCIPLINE_ELECTRICALENGINEERING, 'Electrical Engineering'),
         (DISCIPLINE_MECHANICALENGINEERING, 'Mechanical Engineering'),
         (DISCIPLINE_CHEMICALENGINEERING, 'Chemical Engineering'),
         (DISCIPLINE_MATERIALSENGINEERING, 'Materials Engineering'),
         (DISCIPLINE_MEDICALENGINEERING, 'Medical Engineering'),
         (DISCIPLINE_ENVIRONMENTALENGINEERING, 'Environmental Engineering'),
         (DISCIPLINE_INDUSTRIALENGINEERING, 'Industrial Engineering'),
     )
    ),
    ('Medical Sciences',
     (
         (DISCIPLINE_MEDICINE, 'Basic Medicine'),
         (DISCIPLINE_CLINICAL, 'Clinical Medicine'),
         (DISCIPLINE_HEALTH, 'Health Sciences'),
     )
    ),
    ('Agricultural Sciences',
     (
         (DISCIPLINE_AGRICULTURAL, 'Agriculture, Forestry and Fisheries'),
         (DISCIPLINE_VETERINARY, 'Veterinary Science'),
     )
    ),
    ('Social Sciences',
     (
         (DISCIPLINE_ECONOMICS, 'Economics'),
         (DISCIPLINE_GEOGRAPHY, 'Geography'),
         (DISCIPLINE_LAW, 'Law'),
         (DISCIPLINE_MEDIA, 'Media and Communications'),
         (DISCIPLINE_PEDAGOGY, 'Pedagogy and Educational Sciences'),
         (DISCIPLINE_POLITICALSCIENCE, 'Political Science'),
         (DISCIPLINE_PSYCHOLOGY, 'Psychology'),
         (DISCIPLINE_SOCIOLOGY, 'Sociology'),
     )
    ),
    ('Humanities',
     (
         (DISCIPLINE_ART, 'Art (arts, history or arts, performing arts, music)'),
         (DISCIPLINE_HISTORY, 'History and Archeology'),
         (DISCIPLINE_LITERATURE, 'Language and Literature'),
         (DISCIPLINE_PHILOSOPHY, 'Philosophy, Ethics and Religion'),
     )
    )
)


# The subject areas should use the long version of the discipline as first tuple item
# for each element in the list (so 'Physics' and not 'physics', etc).
SCIPOST_SUBJECT_AREAS = (
    ('Physics', (
        ('Phys:AE', 'Atomic, Molecular and Optical Physics - Experiment'),
        ('Phys:AT', 'Atomic, Molecular and Optical Physics - Theory'),
        ('Phys:BI', 'Biophysics'),
        ('Phys:CE', 'Condensed Matter Physics - Experiment'),
        ('Phys:CT', 'Condensed Matter Physics - Theory'),
        ('Phys:CC', 'Condensed Matter Physics - Computational'),
        ('Phys:FD', 'Fluid Dynamics'),
        ('Phys:GR', 'Gravitation, Cosmology and Astroparticle Physics'),
        ('Phys:HE', 'High-Energy Physics - Experiment'),
        ('Phys:HT', 'High-Energy Physics - Theory'),
        ('Phys:HP', 'High-Energy Physics - Phenomenology'),
        ('Phys:MP', 'Mathematical Physics'),
        ('Phys:NE', 'Nuclear Physics - Experiment'),
        ('Phys:NT', 'Nuclear Physics - Theory'),
        ('Phys:QP', 'Quantum Physics'),
        ('Phys:SM', 'Statistical and Soft Matter Physics'))
    ),
    ('Astrophysics', (
        ('Astro:GA', 'Astrophysics of Galaxies'),
        ('Astro:CO', 'Cosmology and Nongalactic Astrophysics'),
        ('Astro:EP', 'Earth and Planetary Astrophysics'),
        ('Astro:HE', 'High Energy Astrophysical Phenomena'),
        ('Astro:IM', 'Instrumentation and Methods for Astrophysics'),
        ('Astro:SR', 'Solar and Stellar Astrophysics'))
    ),
    ('Chemistry', (
        ('Chem:BI', 'Biochemistry'),
        ('Chem:IN', 'Inorganic Chemistry'),
        ('Chem:OR', 'Organic Chemistry'),
        ('Chem:PH', 'Physical Chemistry'),
        ('Chem:MA', 'Materials Chemistry'),
        ('Chem:TC', 'Theoretical and Computational Chemistry'),
        ('Chem:CE', 'Chemical Engineering'),
        ('Chem:AN', 'Analytical Chemistry'),
        ('Chem:NA', 'Nanoscience'),
        ('Chem:EN', 'Environmental Chemistry'),
        ('Chem:NU', 'Nuclear Chemistry'))
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
        ('Math:SG', 'Symplectic Geometry'))
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
        ('Comp:SY', 'Systems and Control'))
    )
)

subject_areas_raw_dict = dict(SCIPOST_SUBJECT_AREAS)

# Make dict of the form {'Phys:AT': 'Atomic...', ...}
subject_areas_dict = {}
for k in subject_areas_raw_dict.keys():
    subject_areas_dict.update(dict(subject_areas_raw_dict[k]))


APPROACH_THEORETICAL = 'theoretical'
APPROACH_EXPERIMENTAL = 'experimental'
APPROACH_COMPUTATIONAL = 'computational'
APPROACH_PHENOMENOLOGICAL = 'phenomenological'
APPROACH_OBSERVATIONAL = 'observational'
APPROACH_CLINICAL = 'clinical'

SCIPOST_APPROACHES = (
    (APPROACH_THEORETICAL, 'Theoretical'),
    (APPROACH_EXPERIMENTAL, 'Experimental'),
    (APPROACH_COMPUTATIONAL, 'Computational'),
    (APPROACH_PHENOMENOLOGICAL, 'Phenomenological'),
    (APPROACH_OBSERVATIONAL, 'Observational'),
    (APPROACH_CLINICAL, 'Clinical'),
)


# Contributor types
NEWLY_REGISTERED, NORMAL_CONTRIBUTOR = 'newly_registered', 'normal'
UNVERIFIABLE_CREDENTIALS, NO_SCIENTIST = 'unverifiable', 'no_scientist'
DOUBLE_ACCOUNT, OUT_OF_ACADEMIA = 'double_account', 'out_of_academia'
BARRED, DISABLED, DECEASED = 'barred', 'disabled', 'deceased'
CONTRIBUTOR_STATUSES = (
    (NEWLY_REGISTERED, 'Newly registered'),
    (NORMAL_CONTRIBUTOR, 'Normal user'),
    (UNVERIFIABLE_CREDENTIALS, 'Unverifiable credentials'),
    (NO_SCIENTIST, 'Not a professional scientist'),
    (DOUBLE_ACCOUNT, 'Other account already exists'),
    (OUT_OF_ACADEMIA, 'Out of academia'),
    (BARRED, 'Barred from SciPost'),
    (DISABLED, 'Account disabled'),
    (DECEASED, 'Person deceased')
)

TITLE_DR = 'DR'
TITLE_CHOICES = (
    ('PR', 'Prof.'),
    ('DR', 'Dr'),
    ('MR', 'Mr'),
    ('MRS', 'Mrs'),
    ('MS', 'Ms'),
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
