# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-02-14 01:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("finances", "0008_subsidy_amount_publicly_shown"),
    ]

    operations = [
        migrations.AlterField(
            model_name="subsidy",
            name="subsidy_type",
            field=models.CharField(
                choices=[
                    ("sponsorshipagreement", "Sponsorship Agreement"),
                    ("incidentalgrant", "Incidental Grant"),
                    ("developmentgrant", "Development Grant"),
                    ("collaborationagreement", "Collaboration Agreement"),
                    ("donation", "Donation"),
                    ("grant", "Grant"),
                    ("partneragreement", "Partner Agreement"),
                ],
                max_length=256,
            ),
        ),
    ]
