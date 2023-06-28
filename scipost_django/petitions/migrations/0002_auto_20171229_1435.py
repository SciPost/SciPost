# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-29 13:35
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("petitions", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("scipost", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="petitionsignatory",
            name="signatory",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="petition_signatories",
                to="scipost.Contributor",
            ),
        ),
        migrations.AddField(
            model_name="petition",
            name="creator",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
