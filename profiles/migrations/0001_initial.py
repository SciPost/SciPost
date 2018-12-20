# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-16 09:35
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import scipost.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(choices=[('PR', 'Prof.'), ('DR', 'Dr'), ('MR', 'Mr'), ('MRS', 'Mrs'), ('MS', 'Ms')], max_length=4)),
                ('first_name', models.CharField(max_length=64)),
                ('last_name', models.CharField(max_length=64)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('discipline', models.CharField(choices=[('physics', 'Physics'), ('astrophysics', 'Astrophysics'), ('mathematics', 'Mathematics'), ('computerscience', 'Computer Science')], default='physics', max_length=20, verbose_name='Main discipline')),
                ('expertises', scipost.fields.ChoiceArrayField(base_field=models.CharField(choices=[('Physics', (('Phys:AE', 'Atomic, Molecular and Optical Physics - Experiment'), ('Phys:AT', 'Atomic, Molecular and Optical Physics - Theory'), ('Phys:BI', 'Biophysics'), ('Phys:CE', 'Condensed Matter Physics - Experiment'), ('Phys:CT', 'Condensed Matter Physics - Theory'), ('Phys:FD', 'Fluid Dynamics'), ('Phys:GR', 'Gravitation, Cosmology and Astroparticle Physics'), ('Phys:HE', 'High-Energy Physics - Experiment'), ('Phys:HT', 'High-Energy Physics - Theory'), ('Phys:HP', 'High-Energy Physics - Phenomenology'), ('Phys:MP', 'Mathematical Physics'), ('Phys:NE', 'Nuclear Physics - Experiment'), ('Phys:NT', 'Nuclear Physics - Theory'), ('Phys:QP', 'Quantum Physics'), ('Phys:SM', 'Statistical and Soft Matter Physics'))), ('Astrophysics', (('Astro:GA', 'Astrophysics of Galaxies'), ('Astro:CO', 'Cosmology and Nongalactic Astrophysics'), ('Astro:EP', 'Earth and Planetary Astrophysics'), ('Astro:HE', 'High Energy Astrophysical Phenomena'), ('Astro:IM', 'Instrumentation and Methods for Astrophysics'), ('Astro:SR', 'Solar and Stellar Astrophysics'))), ('Mathematics', (('Math:AG', 'Algebraic Geometry'), ('Math:AT', 'Algebraic Topology'), ('Math:AP', 'Analysis of PDEs'), ('Math:CT', 'Category Theory'), ('Math:CA', 'Classical Analysis and ODEs'), ('Math:CO', 'Combinatorics'), ('Math:AC', 'Commutative Algebra'), ('Math:CV', 'Complex Variables'), ('Math:DG', 'Differential Geometry'), ('Math:DS', 'Dynamical Systems'), ('Math:FA', 'Functional Analysis'), ('Math:GM', 'General Mathematics'), ('Math:GN', 'General Topology'), ('Math:GT', 'Geometric Topology'), ('Math:GR', 'Group Theory'), ('Math:HO', 'History and Overview'), ('Math:IT', 'Information Theory'), ('Math:KT', 'K-Theory and Homology'), ('Math:LO', 'Logic'), ('Math:MP', 'Mathematical Physics'), ('Math:MG', 'Metric Geometry'), ('Math:NT', 'Number Theory'), ('Math:NA', 'Numerical Analysis'), ('Math:OA', 'Operator Algebras'), ('Math:OC', 'Optimization and Control'), ('Math:PR', 'Probability'), ('Math:QA', 'Quantum Algebra'), ('Math:RT', 'Representation Theory'), ('Math:RA', 'Rings and Algebras'), ('Math:SP', 'Spectral Theory'), ('Math:ST', 'Statistics Theory'), ('Math:SG', 'Symplectic Geometry'))), ('Computer Science', (('Comp:AI', 'Artificial Intelligence'), ('Comp:CC', 'Computational Complexity'), ('Comp:CE', 'Computational Engineering, Finance, and Science'), ('Comp:CG', 'Computational Geometry'), ('Comp:GT', 'Computer Science and Game Theory'), ('Comp:CV', 'Computer Vision and Pattern Recognition'), ('Comp:CY', 'Computers and Society'), ('Comp:CR', 'Cryptography and Security'), ('Comp:DS', 'Data Structures and Algorithms'), ('Comp:DB', 'Databases'), ('Comp:DL', 'Digital Libraries'), ('Comp:DM', 'Discrete Mathematics'), ('Comp:DC', 'Distributed, Parallel, and Cluster Computing'), ('Comp:ET', 'Emerging Technologies'), ('Comp:FL', 'Formal Languages and Automata Theory'), ('Comp:GL', 'General Literature'), ('Comp:GR', 'Graphics'), ('Comp:AR', 'Hardware Architecture'), ('Comp:HC', 'Human-Computer Interaction'), ('Comp:IR', 'Information Retrieval'), ('Comp:IT', 'Information Theory'), ('Comp:LG', 'Learning'), ('Comp:LO', 'Logic in Computer Science'), ('Comp:MS', 'Mathematical Software'), ('Comp:MA', 'Multiagent Systems'), ('Comp:MM', 'Multimedia'), ('Comp:NI', 'Networking and Internet Architecture'), ('Comp:NE', 'Neural and Evolutionary Computing'), ('Comp:NA', 'Numerical Analysis'), ('Comp:OS', 'Operating Systems'), ('Comp:OH', 'Other Computer Science'), ('Comp:PF', 'Performance'), ('Comp:PL', 'Programming Languages'), ('Comp:RO', 'Robotics'), ('Comp:SI', 'Social and Information Networks'), ('Comp:SE', 'Software Engineering'), ('Comp:SD', 'Sound'), ('Comp:SC', 'Symbolic Computation'), ('Comp:SY', 'Systems and Control')))], max_length=10), blank=True, null=True, size=None)),
                ('orcid_id', models.CharField(blank=True, max_length=20, validators=[django.core.validators.RegexValidator('^[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X]{1}$', 'Please follow the ORCID format, e.g.: 0000-0001-2345-6789')], verbose_name='ORCID id')),
                ('webpage', models.URLField(blank=True)),
                ('accepts_SciPost_emails', models.BooleanField(default=True)),
                ('accepts_refereeing_requests', models.BooleanField(default=True)),
            ],
        ),
    ]