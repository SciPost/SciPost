# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-17 13:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invitations', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='registrationinvitation',
            name='date_sent_first',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='registrationinvitation',
            name='date_sent_last',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]