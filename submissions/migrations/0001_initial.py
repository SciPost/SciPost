# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-29 13:35
from __future__ import unicode_literals

import datetime
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import scipost.db.fields
import scipost.fields
import submissions.behaviors


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('proceedings', '0001_initial'),
        ('colleges', '0001_initial'),
        ('scipost', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EditorialAssignment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accepted', models.NullBooleanField(choices=[(None, 'Response pending'), (True, 'Accept'), (False, 'Decline')], default=None)),
                ('deprecated', models.BooleanField(default=False)),
                ('completed', models.BooleanField(default=False)),
                ('refusal_reason', models.CharField(blank=True, choices=[('BUS', 'Too busy'), ('VAC', 'Away on vacation'), ('COI', 'Conflict of interest: coauthor in last 5 years'), ('CCC', 'Conflict of interest: close colleague'), ('NIR', 'Cannot give an impartial assessment'), ('OFE', 'Outside of my field of expertise'), ('NIE', 'Not interested enough'), ('DNP', 'SciPost should not even consider this paper')], max_length=3, null=True)),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('date_answered', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'default_related_name': 'editorial_assignments',
                'ordering': ['-date_created'],
            },
            bases=(submissions.behaviors.SubmissionRelatedObjectMixin, models.Model),
        ),
        migrations.CreateModel(
            name='EditorialCommunication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comtype', models.CharField(choices=[('EtoA', 'Editor-in-charge to Author'), ('EtoR', 'Editor-in-charge to Referee'), ('EtoS', 'Editor-in-charge to SciPost Editorial Administration'), ('AtoE', 'Author to Editor-in-charge'), ('RtoE', 'Referee to Editor-in-Charge'), ('StoE', 'SciPost Editorial Administration to Editor-in-charge')], max_length=4)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('text', models.TextField()),
                ('referee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='referee_in_correspondence', to='scipost.Contributor')),
            ],
            options={
                'ordering': ['timestamp'],
            },
            bases=(submissions.behaviors.SubmissionRelatedObjectMixin, models.Model),
        ),
        migrations.CreateModel(
            name='EICRecommendation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_submitted', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date submitted')),
                ('remarks_for_authors', models.TextField(blank=True, null=True)),
                ('requested_changes', models.TextField(blank=True, null=True, verbose_name='requested changes')),
                ('remarks_for_editorial_college', models.TextField(blank=True, verbose_name='optional remarks for the Editorial College')),
                ('recommendation', models.SmallIntegerField(choices=[(None, '-'), (1, 'Publish as Tier I (top 10% of papers in this journal, qualifies as Select) NOTE: SELECT NOT YET OPEN, STARTS EARLY 2017'), (2, 'Publish as Tier II (top 50% of papers in this journal)'), (3, 'Publish as Tier III (meets the criteria of this journal)'), (-1, 'Ask for minor revision'), (-2, 'Ask for major revision'), (-3, 'Reject')])),
                ('voting_deadline', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date submitted')),
                ('eligible_to_vote', models.ManyToManyField(blank=True, related_name='eligible_to_vote', to='scipost.Contributor')),
            ],
            bases=(submissions.behaviors.SubmissionRelatedObjectMixin, models.Model),
        ),
        migrations.CreateModel(
            name='iThenticateReport',
            fields=[
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('latest_activity', scipost.db.fields.AutoDateTimeField(blank=True, default=django.utils.timezone.now, editable=False)),
                ('uploaded_time', models.DateTimeField(blank=True, null=True)),
                ('processed_time', models.DateTimeField(blank=True, null=True)),
                ('doc_id', models.IntegerField(primary_key=True, serialize=False)),
                ('part_id', models.IntegerField(blank=True, null=True)),
                ('percent_match', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'iThenticate Report',
                'verbose_name_plural': 'iThenticate Reports',
            },
        ),
        migrations.CreateModel(
            name='RefereeInvitation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(choices=[('PR', 'Prof.'), ('DR', 'Dr'), ('MR', 'Mr'), ('MRS', 'Mrs'), ('MS', 'Ms')], max_length=4)),
                ('first_name', models.CharField(default='', max_length=30)),
                ('last_name', models.CharField(default='', max_length=30)),
                ('email_address', models.EmailField(max_length=254)),
                ('invitation_key', models.CharField(default='', max_length=40)),
                ('date_invited', models.DateTimeField(default=django.utils.timezone.now)),
                ('nr_reminders', models.PositiveSmallIntegerField(default=0)),
                ('date_last_reminded', models.DateTimeField(blank=True, null=True)),
                ('accepted', models.NullBooleanField(choices=[(None, 'Response pending'), (True, 'Accept'), (False, 'Decline')], default=None)),
                ('date_responded', models.DateTimeField(blank=True, null=True)),
                ('refusal_reason', models.CharField(blank=True, choices=[('BUS', 'Too busy'), ('VAC', 'Away on vacation'), ('COI', 'Conflict of interest: coauthor in last 5 years'), ('CCC', 'Conflict of interest: close colleague'), ('NIR', 'Cannot give an impartial assessment'), ('OFE', 'Outside of my field of expertise'), ('NIE', 'Not interested enough'), ('DNP', 'SciPost should not even consider this paper')], max_length=3, null=True)),
                ('fulfilled', models.BooleanField(default=False)),
                ('cancelled', models.BooleanField(default=False)),
                ('invited_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='referee_invited_by', to='scipost.Contributor')),
                ('referee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='referee_invitations', to='scipost.Contributor')),
            ],
            bases=(submissions.behaviors.SubmissionRelatedObjectMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('vetted', 'Vetted'), ('unvetted', 'Unvetted'), ('incorrect', 'Rejected (incorrect)'), ('unclear', 'Rejected (unclear)'), ('notuseful', 'Rejected (not useful)'), ('notacademic', 'Rejected (not academic in style)')], default='unvetted', max_length=16)),
                ('report_nr', models.PositiveSmallIntegerField(default=0, help_text='This number is a unique number refeering to the Report nr. of the Submission')),
                ('invited', models.BooleanField(default=False)),
                ('flagged', models.BooleanField(default=False)),
                ('date_submitted', models.DateTimeField(verbose_name='date submitted')),
                ('qualification', models.PositiveSmallIntegerField(choices=[(None, '-'), (4, 'expert in this subject'), (3, 'very knowledgeable in this subject'), (2, 'knowledgeable in this subject'), (1, 'generally qualified'), (0, 'not qualified')], verbose_name='Qualification to referee this: I am')),
                ('strengths', models.TextField(blank=True)),
                ('weaknesses', models.TextField(blank=True)),
                ('report', models.TextField()),
                ('requested_changes', models.TextField(blank=True, verbose_name='requested changes')),
                ('validity', models.PositiveSmallIntegerField(blank=True, choices=[(None, '-'), (100, 'top'), (80, 'high'), (60, 'good'), (40, 'ok'), (20, 'low'), (0, 'poor')], null=True)),
                ('significance', models.PositiveSmallIntegerField(blank=True, choices=[(None, '-'), (100, 'top'), (80, 'high'), (60, 'good'), (40, 'ok'), (20, 'low'), (0, 'poor')], null=True)),
                ('originality', models.PositiveSmallIntegerField(blank=True, choices=[(None, '-'), (100, 'top'), (80, 'high'), (60, 'good'), (40, 'ok'), (20, 'low'), (0, 'poor')], null=True)),
                ('clarity', models.PositiveSmallIntegerField(blank=True, choices=[(None, '-'), (100, 'top'), (80, 'high'), (60, 'good'), (40, 'ok'), (20, 'low'), (0, 'poor')], null=True)),
                ('formatting', models.SmallIntegerField(blank=True, choices=[(None, '-'), (6, 'perfect'), (5, 'excellent'), (4, 'good'), (3, 'reasonable'), (2, 'acceptable'), (1, 'below threshold'), (0, 'mediocre')], null=True, verbose_name='Quality of paper formatting')),
                ('grammar', models.SmallIntegerField(blank=True, choices=[(None, '-'), (6, 'perfect'), (5, 'excellent'), (4, 'good'), (3, 'reasonable'), (2, 'acceptable'), (1, 'below threshold'), (0, 'mediocre')], null=True, verbose_name='Quality of English grammar')),
                ('recommendation', models.SmallIntegerField(choices=[(None, '-'), (1, 'Publish as Tier I (top 10% of papers in this journal, qualifies as Select) NOTE: SELECT NOT YET OPEN, STARTS EARLY 2017'), (2, 'Publish as Tier II (top 50% of papers in this journal)'), (3, 'Publish as Tier III (meets the criteria of this journal)'), (-1, 'Ask for minor revision'), (-2, 'Ask for major revision'), (-3, 'Reject')])),
                ('remarks_for_editors', models.TextField(blank=True, verbose_name='optional remarks for the Editors only')),
                ('needs_doi', models.NullBooleanField(default=None)),
                ('doideposit_needs_updating', models.BooleanField(default=False)),
                ('doi_label', models.CharField(blank=True, max_length=200)),
                ('anonymous', models.BooleanField(default=True, verbose_name='Publish anonymously')),
                ('pdf_report', models.FileField(blank=True, max_length=200, upload_to='UPLOADS/REPORTS/%Y/%m/')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='scipost.Contributor')),
            ],
            options={
                'default_related_name': 'reports',
                'ordering': ['-date_submitted'],
            },
            bases=(submissions.behaviors.SubmissionRelatedObjectMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('author_comments', models.TextField(blank=True)),
                ('author_list', models.CharField(max_length=1000, verbose_name='author list')),
                ('discipline', models.CharField(choices=[('physics', 'Physics'), ('astrophysics', 'Astrophysics'), ('mathematics', 'Mathematics'), ('computerscience', 'Computer Science')], default='physics', max_length=20)),
                ('domain', models.CharField(choices=[('E', 'Experimental'), ('T', 'Theoretical'), ('C', 'Computational'), ('ET', 'Exp. & Theor.'), ('EC', 'Exp. & Comp.'), ('TC', 'Theor. & Comp.'), ('ETC', 'Exp., Theor. & Comp.')], max_length=3)),
                ('is_current', models.BooleanField(default=True)),
                ('is_resubmission', models.BooleanField(default=False)),
                ('list_of_changes', models.TextField(blank=True)),
                ('open_for_commenting', models.BooleanField(default=False)),
                ('open_for_reporting', models.BooleanField(default=False)),
                ('referees_flagged', models.TextField(blank=True)),
                ('referees_suggested', models.TextField(blank=True)),
                ('remarks_for_editors', models.TextField(blank=True)),
                ('reporting_deadline', models.DateTimeField(default=django.utils.timezone.now)),
                ('secondary_areas', scipost.fields.ChoiceArrayField(base_field=models.CharField(choices=[('Physics', (('Phys:AE', 'Atomic, Molecular and Optical Physics - Experiment'), ('Phys:AT', 'Atomic, Molecular and Optical Physics - Theory'), ('Phys:BI', 'Biophysics'), ('Phys:CE', 'Condensed Matter Physics - Experiment'), ('Phys:CT', 'Condensed Matter Physics - Theory'), ('Phys:FD', 'Fluid Dynamics'), ('Phys:GR', 'Gravitation, Cosmology and Astroparticle Physics'), ('Phys:HE', 'High-Energy Physics - Experiment'), ('Phys:HT', 'High-Energy Physics - Theory'), ('Phys:HP', 'High-Energy Physics - Phenomenology'), ('Phys:MP', 'Mathematical Physics'), ('Phys:NE', 'Nuclear Physics - Experiment'), ('Phys:NT', 'Nuclear Physics - Theory'), ('Phys:QP', 'Quantum Physics'), ('Phys:SM', 'Statistical and Soft Matter Physics'))), ('Astrophysics', (('Astro:GA', 'Astrophysics of Galaxies'), ('Astro:CO', 'Cosmology and Nongalactic Astrophysics'), ('Astro:EP', 'Earth and Planetary Astrophysics'), ('Astro:HE', 'High Energy Astrophysical Phenomena'), ('Astro:IM', 'Instrumentation and Methods for Astrophysics'), ('Astro:SR', 'Solar and Stellar Astrophysics'))), ('Mathematics', (('Math:AG', 'Algebraic Geometry'), ('Math:AT', 'Algebraic Topology'), ('Math:AP', 'Analysis of PDEs'), ('Math:CT', 'Category Theory'), ('Math:CA', 'Classical Analysis and ODEs'), ('Math:CO', 'Combinatorics'), ('Math:AC', 'Commutative Algebra'), ('Math:CV', 'Complex Variables'), ('Math:DG', 'Differential Geometry'), ('Math:DS', 'Dynamical Systems'), ('Math:FA', 'Functional Analysis'), ('Math:GM', 'General Mathematics'), ('Math:GN', 'General Topology'), ('Math:GT', 'Geometric Topology'), ('Math:GR', 'Group Theory'), ('Math:HO', 'History and Overview'), ('Math:IT', 'Information Theory'), ('Math:KT', 'K-Theory and Homology'), ('Math:LO', 'Logic'), ('Math:MP', 'Mathematical Physics'), ('Math:MG', 'Metric Geometry'), ('Math:NT', 'Number Theory'), ('Math:NA', 'Numerical Analysis'), ('Math:OA', 'Operator Algebras'), ('Math:OC', 'Optimization and Control'), ('Math:PR', 'Probability'), ('Math:QA', 'Quantum Algebra'), ('Math:RT', 'Representation Theory'), ('Math:RA', 'Rings and Algebras'), ('Math:SP', 'Spectral Theory'), ('Math:ST', 'Statistics Theory'), ('Math:SG', 'Symplectic Geometry'))), ('Computer Science', (('Comp:AI', 'Artificial Intelligence'), ('Comp:CC', 'Computational Complexity'), ('Comp:CE', 'Computational Engineering, Finance, and Science'), ('Comp:CG', 'Computational Geometry'), ('Comp:GT', 'Computer Science and Game Theory'), ('Comp:CV', 'Computer Vision and Pattern Recognition'), ('Comp:CY', 'Computers and Society'), ('Comp:CR', 'Cryptography and Security'), ('Comp:DS', 'Data Structures and Algorithms'), ('Comp:DB', 'Databases'), ('Comp:DL', 'Digital Libraries'), ('Comp:DM', 'Discrete Mathematics'), ('Comp:DC', 'Distributed, Parallel, and Cluster Computing'), ('Comp:ET', 'Emerging Technologies'), ('Comp:FL', 'Formal Languages and Automata Theory'), ('Comp:GL', 'General Literature'), ('Comp:GR', 'Graphics'), ('Comp:AR', 'Hardware Architecture'), ('Comp:HC', 'Human-Computer Interaction'), ('Comp:IR', 'Information Retrieval'), ('Comp:IT', 'Information Theory'), ('Comp:LG', 'Learning'), ('Comp:LO', 'Logic in Computer Science'), ('Comp:MS', 'Mathematical Software'), ('Comp:MA', 'Multiagent Systems'), ('Comp:MM', 'Multimedia'), ('Comp:NI', 'Networking and Internet Architecture'), ('Comp:NE', 'Neural and Evolutionary Computing'), ('Comp:NA', 'Numerical Analysis'), ('Comp:OS', 'Operating Systems'), ('Comp:OH', 'Other Computer Science'), ('Comp:PF', 'Performance'), ('Comp:PL', 'Programming Languages'), ('Comp:RO', 'Robotics'), ('Comp:SI', 'Social and Information Networks'), ('Comp:SE', 'Software Engineering'), ('Comp:SD', 'Sound'), ('Comp:SC', 'Symbolic Computation'), ('Comp:SY', 'Systems and Control')))], max_length=10), blank=True, null=True, size=None)),
                ('status', models.CharField(choices=[('unassigned', 'Unassigned, undergoing pre-screening'), ('resubmitted_incoming', 'Resubmission incoming'), ('assignment_failed', 'Failed to assign Editor-in-charge; manuscript rejected'), ('EICassigned', 'Editor-in-charge assigned, manuscript under review'), ('review_closed', 'Review period closed, editorial recommendation pending'), ('revision_requested', 'Editor-in-charge has requested revision'), ('resubmitted', 'Has been resubmitted'), ('resubmitted_and_rejected', 'Has been resubmitted and subsequently rejected'), ('resubmitted_and_rejected_visible', 'Has been resubmitted and subsequently rejected (still publicly visible)'), ('voting_in_preparation', 'Voting in preparation (eligible Fellows being selected)'), ('put_to_EC_voting', 'Undergoing voting at the Editorial College'), ('awaiting_ed_rec', 'Awaiting Editorial Recommendation'), ('EC_vote_completed', 'Editorial College voting rounded up'), ('accepted', 'Publication decision taken: accept'), ('rejected', 'Publication decision taken: reject'), ('rejected_visible', 'Publication decision taken: reject (still publicly visible)'), ('published', 'Published'), ('withdrawn', 'Withdrawn by the Authors')], default='unassigned', max_length=30)),
                ('refereeing_cycle', models.CharField(choices=[('default', 'Default cycle'), ('short', 'Short cycle'), ('direct_rec', 'Direct editorial recommendation')], default='default', max_length=30)),
                ('subject_area', models.CharField(choices=[('Physics', (('Phys:AE', 'Atomic, Molecular and Optical Physics - Experiment'), ('Phys:AT', 'Atomic, Molecular and Optical Physics - Theory'), ('Phys:BI', 'Biophysics'), ('Phys:CE', 'Condensed Matter Physics - Experiment'), ('Phys:CT', 'Condensed Matter Physics - Theory'), ('Phys:FD', 'Fluid Dynamics'), ('Phys:GR', 'Gravitation, Cosmology and Astroparticle Physics'), ('Phys:HE', 'High-Energy Physics - Experiment'), ('Phys:HT', 'High-Energy Physics - Theory'), ('Phys:HP', 'High-Energy Physics - Phenomenology'), ('Phys:MP', 'Mathematical Physics'), ('Phys:NE', 'Nuclear Physics - Experiment'), ('Phys:NT', 'Nuclear Physics - Theory'), ('Phys:QP', 'Quantum Physics'), ('Phys:SM', 'Statistical and Soft Matter Physics'))), ('Astrophysics', (('Astro:GA', 'Astrophysics of Galaxies'), ('Astro:CO', 'Cosmology and Nongalactic Astrophysics'), ('Astro:EP', 'Earth and Planetary Astrophysics'), ('Astro:HE', 'High Energy Astrophysical Phenomena'), ('Astro:IM', 'Instrumentation and Methods for Astrophysics'), ('Astro:SR', 'Solar and Stellar Astrophysics'))), ('Mathematics', (('Math:AG', 'Algebraic Geometry'), ('Math:AT', 'Algebraic Topology'), ('Math:AP', 'Analysis of PDEs'), ('Math:CT', 'Category Theory'), ('Math:CA', 'Classical Analysis and ODEs'), ('Math:CO', 'Combinatorics'), ('Math:AC', 'Commutative Algebra'), ('Math:CV', 'Complex Variables'), ('Math:DG', 'Differential Geometry'), ('Math:DS', 'Dynamical Systems'), ('Math:FA', 'Functional Analysis'), ('Math:GM', 'General Mathematics'), ('Math:GN', 'General Topology'), ('Math:GT', 'Geometric Topology'), ('Math:GR', 'Group Theory'), ('Math:HO', 'History and Overview'), ('Math:IT', 'Information Theory'), ('Math:KT', 'K-Theory and Homology'), ('Math:LO', 'Logic'), ('Math:MP', 'Mathematical Physics'), ('Math:MG', 'Metric Geometry'), ('Math:NT', 'Number Theory'), ('Math:NA', 'Numerical Analysis'), ('Math:OA', 'Operator Algebras'), ('Math:OC', 'Optimization and Control'), ('Math:PR', 'Probability'), ('Math:QA', 'Quantum Algebra'), ('Math:RT', 'Representation Theory'), ('Math:RA', 'Rings and Algebras'), ('Math:SP', 'Spectral Theory'), ('Math:ST', 'Statistics Theory'), ('Math:SG', 'Symplectic Geometry'))), ('Computer Science', (('Comp:AI', 'Artificial Intelligence'), ('Comp:CC', 'Computational Complexity'), ('Comp:CE', 'Computational Engineering, Finance, and Science'), ('Comp:CG', 'Computational Geometry'), ('Comp:GT', 'Computer Science and Game Theory'), ('Comp:CV', 'Computer Vision and Pattern Recognition'), ('Comp:CY', 'Computers and Society'), ('Comp:CR', 'Cryptography and Security'), ('Comp:DS', 'Data Structures and Algorithms'), ('Comp:DB', 'Databases'), ('Comp:DL', 'Digital Libraries'), ('Comp:DM', 'Discrete Mathematics'), ('Comp:DC', 'Distributed, Parallel, and Cluster Computing'), ('Comp:ET', 'Emerging Technologies'), ('Comp:FL', 'Formal Languages and Automata Theory'), ('Comp:GL', 'General Literature'), ('Comp:GR', 'Graphics'), ('Comp:AR', 'Hardware Architecture'), ('Comp:HC', 'Human-Computer Interaction'), ('Comp:IR', 'Information Retrieval'), ('Comp:IT', 'Information Theory'), ('Comp:LG', 'Learning'), ('Comp:LO', 'Logic in Computer Science'), ('Comp:MS', 'Mathematical Software'), ('Comp:MA', 'Multiagent Systems'), ('Comp:MM', 'Multimedia'), ('Comp:NI', 'Networking and Internet Architecture'), ('Comp:NE', 'Neural and Evolutionary Computing'), ('Comp:NA', 'Numerical Analysis'), ('Comp:OS', 'Operating Systems'), ('Comp:OH', 'Other Computer Science'), ('Comp:PF', 'Performance'), ('Comp:PL', 'Programming Languages'), ('Comp:RO', 'Robotics'), ('Comp:SI', 'Social and Information Networks'), ('Comp:SE', 'Software Engineering'), ('Comp:SD', 'Sound'), ('Comp:SC', 'Symbolic Computation'), ('Comp:SY', 'Systems and Control')))], default='Phys:QP', max_length=10, verbose_name='Primary subject area')),
                ('submission_type', models.CharField(blank=True, choices=[('Letter', 'Letter (broad-interest breakthrough results)'), ('Article', 'Article (in-depth reports on specialized research)'), ('Review', 'Review (candid snapshot of current research in a given area)')], default=None, max_length=10, null=True)),
                ('submitted_to_journal', models.CharField(choices=[('SciPostPhys', 'SciPost Physics'), ('SciPostPhysLectNotes', 'SciPost Physics Lecture Notes'), ('SciPostPhysProc', 'SciPost Physics Proceedings')], max_length=30, verbose_name='Journal to be submitted to')),
                ('title', models.CharField(max_length=300)),
                ('abstract', models.TextField()),
                ('arxiv_identifier_w_vn_nr', models.CharField(default='0000.00000v0', max_length=15)),
                ('arxiv_identifier_wo_vn_nr', models.CharField(default='0000.00000', max_length=10)),
                ('arxiv_vn_nr', models.PositiveSmallIntegerField(default=1)),
                ('arxiv_link', models.URLField(verbose_name='arXiv link (including version nr)')),
                ('pdf_refereeing_pack', models.FileField(blank=True, max_length=200, upload_to='UPLOADS/REFEREE/%Y/%m/')),
                ('metadata', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default={}, null=True)),
                ('submission_date', models.DateField(default=datetime.date.today, verbose_name='submission date')),
                ('acceptance_date', models.DateField(blank=True, null=True, verbose_name='acceptance date')),
                ('latest_activity', models.DateTimeField(auto_now=True)),
                ('authors', models.ManyToManyField(blank=True, related_name='submissions', to='scipost.Contributor')),
                ('authors_claims', models.ManyToManyField(blank=True, related_name='claimed_submissions', to='scipost.Contributor')),
                ('authors_false_claims', models.ManyToManyField(blank=True, related_name='false_claimed_submissions', to='scipost.Contributor')),
                ('editor_in_charge', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='EIC', to='scipost.Contributor')),
                ('fellows', models.ManyToManyField(blank=True, related_name='pool', to='colleges.Fellowship')),
                ('plagiarism_report', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='to_submission', to='submissions.iThenticateReport')),
                ('proceedings', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='proceedings.Proceedings')),
                ('submitted_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submitted_submissions', to='scipost.Contributor')),
                ('voting_fellows', models.ManyToManyField(blank=True, related_name='voting_pool', to='colleges.Fellowship')),
            ],
        ),
        migrations.CreateModel(
            name='SubmissionEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('latest_activity', scipost.db.fields.AutoDateTimeField(blank=True, default=django.utils.timezone.now, editable=False)),
                ('event', models.CharField(choices=[('gen', 'General comment'), ('eic', 'Comment for Editor-in-charge'), ('auth', 'Comment for author')], default='gen', max_length=4)),
                ('text', models.TextField()),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='submissions.Submission')),
            ],
            options={
                'ordering': ['-created'],
            },
            bases=(submissions.behaviors.SubmissionRelatedObjectMixin, models.Model),
        ),
        migrations.AddField(
            model_name='report',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='submissions.Submission'),
        ),
        migrations.AddField(
            model_name='report',
            name='vetted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='report_vetted_by', to='scipost.Contributor'),
        ),
        migrations.AddField(
            model_name='refereeinvitation',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='referee_invitations', to='submissions.Submission'),
        ),
        migrations.AddField(
            model_name='eicrecommendation',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eicrecommendations', to='submissions.Submission'),
        ),
        migrations.AddField(
            model_name='eicrecommendation',
            name='voted_abstain',
            field=models.ManyToManyField(blank=True, related_name='voted_abstain', to='scipost.Contributor'),
        ),
        migrations.AddField(
            model_name='eicrecommendation',
            name='voted_against',
            field=models.ManyToManyField(blank=True, related_name='voted_against', to='scipost.Contributor'),
        ),
        migrations.AddField(
            model_name='eicrecommendation',
            name='voted_for',
            field=models.ManyToManyField(blank=True, related_name='voted_for', to='scipost.Contributor'),
        ),
        migrations.AddField(
            model_name='editorialcommunication',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='editorial_communications', to='submissions.Submission'),
        ),
        migrations.AddField(
            model_name='editorialassignment',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='editorial_assignments', to='submissions.Submission'),
        ),
        migrations.AddField(
            model_name='editorialassignment',
            name='to',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='editorial_assignments', to='scipost.Contributor'),
        ),
        migrations.AlterUniqueTogether(
            name='report',
            unique_together=set([('submission', 'report_nr')]),
        ),
    ]
