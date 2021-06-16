# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-03-14 15:37
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0024_auto_20180310_1740'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issue',
            name='in_journal',
            field=models.ForeignKey(blank=True, help_text='Assign either an Volume or Journal to the Issue', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='issues', to='journals.Journal'),
        ),
        migrations.AlterField(
            model_name='issue',
            name='in_volume',
            field=models.ForeignKey(blank=True, help_text='Assign either an Volume or Journal to the Issue', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='issues', to='journals.Volume'),
        ),
        migrations.AlterField(
            model_name='publication',
            name='in_issue',
            field=models.ForeignKey(blank=True, help_text='Assign either an Issue or Journal to the Publication', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='publications', to='journals.Issue'),
        ),
        migrations.AlterField(
            model_name='publication',
            name='in_journal',
            field=models.ForeignKey(blank=True, help_text='Assign either an Issue or Journal to the Publication', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='publications', to='journals.Journal'),
        ),
    ]