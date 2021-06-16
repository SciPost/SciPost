# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-03-27 14:14
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0010_auto_20190223_1406'),
        ('profiles', '0017_auto_20190126_2058'),
    ]

    operations = [
        migrations.CreateModel(
            name='Affiliation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('employed_prof_full', 'Full Professor'), ('employed_prof_associate', 'Associate Professor'), ('employed_prof_assistant', 'Assistant Professor'), ('employed_prof_emeritus', 'Emeritus Professor'), ('employed_permanent_staff', 'Permanent Staff'), ('employed_fixed_term_staff', 'Fixed Term Staff'), ('employed_tenure_track', 'Tenure Tracker'), ('employed_postdoc', 'Postdoctoral Researcher'), ('employed_phd', 'PhD candidate'), ('associate_scientist', 'Associate Scientist'), ('consultant', 'Consultant'), ('visitor', 'Visotor')], help_text='Select the most suitable category', max_length=64)),
                ('description', models.CharField(max_length=256)),
                ('date_from', models.DateField(blank=True, null=True)),
                ('date_until', models.DateField(blank=True, null=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='affiliations', to='organizations.Organization')),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='affiliations', to='profiles.Profile')),
            ],
            options={
                'ordering': ['profile__user__last_name', 'profile__user__first_name', 'date_until'],
                'default_related_name': 'affiliations',
            },
        ),
    ]