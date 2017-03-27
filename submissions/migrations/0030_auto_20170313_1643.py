# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-03-13 15:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0029_auto_20170131_1425'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='submissions.Submission'),
        ),
    ]
