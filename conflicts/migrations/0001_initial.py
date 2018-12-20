# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-05-25 07:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('scipost', '0014_auto_20180414_2218'),
        ('journals', '0030_merge_20180519_2204'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConflictOfInterest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('unverified', 'Unverified'), ('verified', 'Verified by Admin'), ('deprecated', 'Deprecated')], default='unverified', max_length=16)),
                ('type', models.CharField(choices=[('coauthor', 'Co-authorship'), ('other', 'Other')], default='other', max_length=16)),
                ('origin', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conflicts', to='scipost.Contributor')),
                ('to_contributor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='scipost.Contributor')),
                ('to_unregistered', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='journals.UnregisteredAuthor')),
            ],
        ),
    ]