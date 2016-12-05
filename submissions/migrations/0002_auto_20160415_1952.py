# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-04-15 17:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0004_auto_20160415_1952'),
        ('submissions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EditorialAssignment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accepted', models.NullBooleanField(choices=[(None, 'Response pending'), (True, 'Accept'), (False, 'Decline')], default=None)),
                ('completed', models.BooleanField(default=False)),
                ('refusal_reason', models.CharField(blank=True, choices=[('BUS', 'Too busy'), ('COI', 'Conflict of interest: coauthor in last 5 years'), ('CCC', 'Conflict of interest: close colleague'), ('NIR', 'Cannot give an impartial assessment'), ('NIE', 'Not interested enough'), ('DNP', 'SciPost should not even consider this paper')], max_length=3, null=True)),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('date_answered', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='EditorialCommunication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('EtoA', 'Editor-in-charge to Author'), ('AtoE', 'Author to Editor-in-charge'), ('EtoR', 'Editor-in-charge to Referee'), ('RtoE', 'Referee to Editor-in-Charge'), ('EtoS', 'Editor-in-charge to SciPost Editorial Administration'), ('StoE', 'SciPost Editorial Administration to Editor-in-charge')], max_length=4)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('text', models.TextField()),
                ('referee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='referee_in_correspondence', to='scipost.Contributor')),
            ],
        ),
        migrations.CreateModel(
            name='EICRecommendation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_submitted', models.DateTimeField(verbose_name='date submitted')),
                ('remarks_for_authors', models.TextField(blank=True, null=True)),
                ('requested_changes', models.TextField(blank=True, null=True, verbose_name='requested changes')),
                ('remarks_for_editorial_college', models.TextField(blank=True, default='', null=True, verbose_name='optional remarks for the Editorial College')),
                ('recommendation', models.SmallIntegerField(choices=[(1, 'Publish as Tier I (top 10% of papers in this journal)'), (2, 'Publish as Tier II (top 50% of papers in this journal)'), (3, 'Publish as Tier III (meets the criteria of this journal)'), (-1, 'Ask for minor revision'), (-2, 'Ask for major revision'), (-3, 'Reject')])),
                ('voting_deadline', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date submitted')),
            ],
        ),
        migrations.CreateModel(
            name='RefereeInvitation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(choices=[('PR', 'Prof.'), ('DR', 'Dr'), ('MR', 'Mr'), ('MRS', 'Mrs')], max_length=4)),
                ('first_name', models.CharField(default='', max_length=30)),
                ('last_name', models.CharField(default='', max_length=30)),
                ('email_address', models.EmailField(max_length=254)),
                ('invitation_key', models.CharField(default='', max_length=40)),
                ('date_invited', models.DateTimeField(default=django.utils.timezone.now)),
                ('accepted', models.NullBooleanField(choices=[(None, 'Response pending'), (True, 'Accept'), (False, 'Decline')], default=None)),
                ('date_responded', models.DateTimeField(blank=True, null=True)),
                ('refusal_reason', models.CharField(blank=True, choices=[('BUS', 'Too busy'), ('COI', 'Conflict of interest: coauthor in last 5 years'), ('CCC', 'Conflict of interest: close colleague'), ('NIR', 'Cannot give an impartial assessment'), ('NIE', 'Not interested enough'), ('DNP', 'SciPost should not even consider this paper')], max_length=3, null=True)),
                ('fulfilled', models.BooleanField(default=False)),
                ('invited_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='referee_invited_by', to='scipost.Contributor')),
                ('referee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='referee', to='scipost.Contributor')),
            ],
        ),
        migrations.RenameField(
            model_name='submission',
            old_name='vetted',
            new_name='assigned',
        ),
        migrations.RemoveField(
            model_name='report',
            name='date_invited',
        ),
        migrations.RemoveField(
            model_name='report',
            name='invited_by',
        ),
        migrations.AddField(
            model_name='report',
            name='invited',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='report',
            name='remarks_for_editors',
            field=models.TextField(blank=True, default='', verbose_name='optional remarks for the Editors only'),
        ),
        migrations.AddField(
            model_name='submission',
            name='reporting_deadline',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='report',
            name='formatting',
            field=models.SmallIntegerField(choices=[(6, 'perfect'), (5, 'excellent'), (4, 'good'), (3, 'reasonable'), (2, 'acceptable'), (1, 'below threshold'), (0, 'mediocre')], verbose_name='Quality of paper formatting'),
        ),
        migrations.AlterField(
            model_name='report',
            name='grammar',
            field=models.SmallIntegerField(choices=[(6, 'perfect'), (5, 'excellent'), (4, 'good'), (3, 'reasonable'), (2, 'acceptable'), (1, 'below threshold'), (0, 'mediocre')], verbose_name='Quality of English grammar'),
        ),
        migrations.AlterField(
            model_name='submission',
            name='editor_in_charge',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='EIC', to='scipost.Contributor'),
        ),
        migrations.AlterField(
            model_name='submission',
            name='status',
            field=models.CharField(choices=[('unassigned', 'Unassigned'), ('assigned', 'Assigned to a specialty editor (response pending)'), ('EICassigned', 'Editor-in-charge assigned, manuscript under review'), ('review_closed', 'Review period closed, editorial recommendation pending'), ('EIC_has_recommended', 'Editor-in-charge has provided recommendation'), ('put_to_EC_voting', 'Undergoing voting at the Editorial College'), ('EC_vote_completed', 'Editorial College voting rounded up'), ('decided', 'Publication decision taken')], max_length=30),
        ),
        migrations.AddField(
            model_name='refereeinvitation',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='submissions.Submission'),
        ),
        migrations.AddField(
            model_name='eicrecommendation',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='submissions.Submission'),
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
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='submissions.Submission'),
        ),
        migrations.AddField(
            model_name='editorialassignment',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='submissions.Submission'),
        ),
        migrations.AddField(
            model_name='editorialassignment',
            name='to',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scipost.Contributor'),
        ),
    ]
