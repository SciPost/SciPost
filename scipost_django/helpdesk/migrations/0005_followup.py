# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-03-14 11:19
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('helpdesk', '0004_auto_20190314_0955'),
    ]

    operations = [
        migrations.CreateModel(
            name='Followup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(blank=True, null=True)),
                ('timestamp', models.DateTimeField()),
                ('action', models.CharField(choices=[('assignment', 'Assignment'), ('reassignment', 'Reassignment'), ('pickup', 'Pickup by handler'), ('respondedtouser', 'Response sent to user'), ('userresonponded', 'User resonponded'), ('markresolved', 'Marked as resolved'), ('markcloseed', 'Mark as closeed')], max_length=32)),
                ('by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ticket_followups', to=settings.AUTH_USER_MODEL)),
                ('ticket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followups', to='helpdesk.Ticket')),
            ],
            options={
                'ordering': ['timestamp'],
            },
        ),
    ]