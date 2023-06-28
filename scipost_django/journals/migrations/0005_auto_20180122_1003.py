# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-01-22 09:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0004_auto_20180121_1202"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="reference",
            options={"ordering": ["reference_number"]},
        ),
        migrations.RenameField(
            model_name="reference",
            old_name="citation_count",
            new_name="reference_number",
        ),
        migrations.AlterField(
            model_name="reference",
            name="citation",
            field=models.CharField(blank=True, max_length=512),
        ),
        migrations.AlterUniqueTogether(
            name="reference",
            unique_together=set([("reference_number", "publication")]),
        ),
    ]
