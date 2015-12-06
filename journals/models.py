from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

from .models import *

#from commentaries.models import *
#from contributors.models import *
#from journals.models import *
#from scipost.models import *


SCIPOST_JOURNALS = (
    ('SciPost Physics Select', 'SciPost Physics Select'),
    ('SciPost Physics Letters', 'SciPost Physics Letters'),
    ('SciPost Physics X', 'SciPost Physics X (cross-division)'),
#    ('SciPost Physics Rapid', 'SciPost Physics Rapid'),
# Possible further specializations: instead of SciPost Physics,
#    ('SciPost Physics A', 'SciPost Physics A (Atomic, Molecular and Optical Physics)'),
#    ('SciPost Physics C', 'SciPost Physics C (Condensed Matter Physics)'),
#    ('SciPost Physics H', 'SciPost Physics H (High-energy Physics)'),
#    ('SciPost Physics M', 'SciPost Physics M (Mathematical Physics)'),
#    ('SciPost Physics N', 'SciPost Physics N (Numerical and Computational Physics)'),
#    ('SciPost Physics Q', 'SciPost Physics Q (Quantum Statistical Mechanics)'),
#    ('SciPost Physics S', 'SciPost Physics S (Classical Statistical and Soft Matter Physics)'), 
# Use the three fundamental branches of Physics: 
#    ('SciPost Physics E', 'SciPost Physics E (Experimental)'),
#    ('SciPost Physics T', 'SciPost Physics T (Theoretical)'),
#    ('SciPost Physics C', 'SciPost Physics C (Computational)'),
# Unified:
    ('SciPost Physics', 'SciPost Physics (Experimental, Theoretical and Computational)'),
    ('SciPost Physics Lecture Notes', 'SciPost Physics Lecture Notes'),
    )

SCIPOST_JOURNALS_SUBMIT = ( # Same as SCIPOST_JOURNALS, but SP Select deactivated
#    ('SciPost Physics Select', 'SciPost Physics Select'), # cannot be submitted to: promoted from Letters
    ('SciPost Physics Letters', 'SciPost Physics Letters'),
#    ('SciPost Physics X', 'SciPost Physics X (cross-division)'), # cannot be submitted to: promoted from SciPost Physics
# Use the three fundamental branches of Physics: 
#    ('SciPost Physics E', 'SciPost Physics E (Experimental)'),
#    ('SciPost Physics T', 'SciPost Physics T (Theoretical)'),
#    ('SciPost Physics C', 'SciPost Physics C (Computational)'),
# Unified:
    ('SciPost Physics', 'SciPost Physics'),
    ('SciPost Physics Lecture Notes', 'SciPost Physics Lecture Notes'),
    )

SCIPOST_JOURNALS_DOMAINS = (
    ('E', 'Experimental'),
    ('T', 'Theoretical'),
    ('C', 'Computational'),
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

