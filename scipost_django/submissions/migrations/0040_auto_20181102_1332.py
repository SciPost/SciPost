# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-11-02 12:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0039_submission_topics'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='author_list',
            field=models.CharField(max_length=10000, verbose_name='author list'),
        ),
    ]