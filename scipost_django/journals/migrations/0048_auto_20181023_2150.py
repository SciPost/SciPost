# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-10-23 19:50
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0047_auto_20181023_0829"),
    ]

    operations = [
        migrations.AlterField(
            model_name="publication",
            name="doi_label",
            field=models.CharField(
                db_index=True,
                max_length=200,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        "^(SciPostPhysProc|SciPostPhysSel|SciPostPhysLectNotes|SciPostPhysCodeb|SciPostPhysComm|SciPostPhys)(.\\w+(.[0-9]+(.[0-9]{3,})?)?)?$",
                        "Only valid DOI expressions are allowed: `[a-zA-Z]+(.\\w+(.[0-9]+(.[0-9]{3,})?)?)?`",
                    )
                ],
            ),
        ),
    ]
