from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User



SCIPOST_JOURNALS = (
    ('SciPost Physics Select', 'SciPost Physics Select'),
    ('SciPost Physics', 'SciPost Physics (Experimental, Theoretical and Computational)'),
    ('SciPost Physics Lecture Notes', 'SciPost Physics Lecture Notes'),
    )

SCIPOST_JOURNALS_SUBMIT = ( # Same as SCIPOST_JOURNALS, but SP Select deactivated
    ('SciPost Physics', 'SciPost Physics'),
    ('SciPost Physics Lecture Notes', 'SciPost Physics Lecture Notes'),
    )
journals_submit_dict = dict(SCIPOST_JOURNALS_SUBMIT)

SCIPOST_JOURNALS_DOMAINS = (
    ('E', 'Experimental'),
    ('T', 'Theoretical'),
    ('C', 'Computational'),
    ('ET', 'Exp. & Theor.'),
    ('EC', 'Exp. & Comp.'),
    ('TC', 'Theor. & Comp.'),
    ('ETC', 'Exp., Theor. & Comp.'), 
)
journals_domains_dict = dict(SCIPOST_JOURNALS_DOMAINS)

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
journals_spec_dict = dict(SCIPOST_JOURNALS_SPECIALIZATIONS)

PHYSICS_SUBJECTS = (
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
