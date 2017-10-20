# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-20 07:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import scipost.db.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('scipost', '0065_authorshipclaim_publication'),
    ]

    operations = [
        migrations.CreateModel(
            name='Fellowship',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('latest_activity', scipost.db.fields.AutoDateTimeField(blank=True, default=django.utils.timezone.now, editable=False)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('until_date', models.DateField(blank=True, null=True)),
                ('guest', models.BooleanField(default=False, verbose_name='Guest Fellowship')),
                ('contributor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fellowships', to='scipost.Contributor')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='fellowship',
            unique_together=set([('contributor', 'start_date', 'until_date')]),
        ),
    ]
