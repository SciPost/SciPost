# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-04-14 18:53
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("invitations", "0012_auto_20180220_2120"),
    ]

    operations = [
        migrations.AlterField(
            model_name="citationnotification",
            name="invitation",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="citation_notifications",
                to="invitations.RegistrationInvitation",
            ),
        ),
    ]
