# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-03-10 06:13
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("forums", "0007_motion"),
    ]

    operations = [
        migrations.AlterField(
            model_name="motion",
            name="post_ptr",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                parent_link=True,
                primary_key=True,
                serialize=False,
                to="forums.Post",
            ),
        ),
    ]
