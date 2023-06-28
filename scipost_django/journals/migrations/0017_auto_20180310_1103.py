# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-03-10 10:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0016_auto_20180303_0918"),
    ]

    operations = [
        migrations.AddField(
            model_name="journal",
            name="_has_issues",
            field=models.BooleanField(
                default=True, verbose_name="Use Issues to group Publications"
            ),
        ),
        migrations.AddField(
            model_name="journal",
            name="_has_volumes",
            field=models.BooleanField(
                default=True,
                verbose_name="Use Issues to group Publications (if True, the use of Issues is required)",
            ),
        ),
        migrations.AlterField(
            model_name="publication",
            name="in_issue",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="publications",
                to="journals.Issue",
            ),
        ),
    ]
