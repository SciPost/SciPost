# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-17 12:48
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('submissions', '0008_auto_20180127_2208'),
        ('journals', '0013_auto_20180216_0850'),
        ('scipost', '0004_auto_20180212_1932'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegistrationInvitation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(choices=[('PR', 'Prof.'), ('DR', 'Dr'), ('MR', 'Mr'), ('MRS', 'Mrs'), ('MS', 'Ms')], max_length=4)),
                ('first_name', models.CharField(max_length=30)),
                ('last_name', models.CharField(max_length=150)),
                ('email', models.EmailField(max_length=254)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('sent', 'Sent'), ('declined', 'Declined'), ('register', 'Registered')], default='draft', max_length=8)),
                ('message_style', models.CharField(choices=[('F', 'Formal'), ('P', 'Personal')], default='F', max_length=1)),
                ('personal_message', models.TextField(blank=True)),
                ('invitation_type', models.CharField(choices=[('F', 'Editorial Fellow'), ('C', 'Contributor'), ('R', 'Refereeing')], default='C', max_length=2)),
                ('invitation_key', models.CharField(max_length=40, unique=True)),
                ('key_expires', models.DateTimeField(default=django.utils.timezone.now)),
                ('date_sent_first', models.DateTimeField(default=django.utils.timezone.now)),
                ('date_sent_last', models.DateTimeField(default=django.utils.timezone.now)),
                ('number_of_reminders', models.PositiveSmallIntegerField(default=0)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('cited_in_publication', models.ManyToManyField(blank=True, related_name='_registrationinvitation_cited_in_publication_+', to='journals.Publication')),
                ('cited_in_submission', models.ManyToManyField(blank=True, related_name='_registrationinvitation_cited_in_submission_+', to='submissions.Submission')),
                ('invited_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='invitations_sent', to='scipost.Contributor')),
            ],
            options={
                'ordering': ['last_name'],
            },
        ),
    ]
