# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-04-27 07:31
from __future__ import unicode_literals

import comments.behaviors
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0010_auto_20180314_1607"),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="file_attachment",
            field=models.FileField(
                blank=True,
                upload_to="uploads/reports/%Y/%m/%d/",
                validators=[
                    comments.behaviors.validate_file_extension,
                    comments.behaviors.validate_max_file_size,
                ],
            ),
        ),
    ]
