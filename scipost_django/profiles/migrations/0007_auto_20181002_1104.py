# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-10-02 09:04
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0006_populate_profile_from_reginv_and_refinv"),
    ]

    operations = [migrations.RenameModel("AlternativeEmail", "ProfileEmail")]
