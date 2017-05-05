# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-04-23 17:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0050_auto_20170416_2152'),
        ('mailing_lists', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='mailchimplist',
            options={'ordering': ['status', 'internal_name', 'name']},
        ),
        migrations.AddField(
            model_name='mailchimplist',
            name='open_for_subscription',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='activemailchimpsubscription',
            name='contributor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mail_subscription', to='scipost.Contributor'),
        ),
        migrations.AlterField(
            model_name='mailchimplist',
            name='mailchimp_list_id',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterUniqueTogether(
            name='activemailchimpsubscription',
            unique_together=set([('active_list', 'contributor')]),
        ),
    ]
