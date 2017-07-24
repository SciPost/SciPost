# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-07-24 15:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import scipost.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0054_auto_20170721_1148'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubmissionEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('latest_activity', scipost.db.fields.AutoDateTimeField(blank=True, default=django.utils.timezone.now, editable=False)),
                ('event', models.CharField(choices=[('gen', 'General comment'), ('eic', 'Comment for Editor-in-charge'), ('auth', 'Comment for author')], default='gen', max_length=4)),
                ('blub', models.TextField()),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='submissions.Submission')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterModelOptions(
            name='editorialcommunication',
            options={'ordering': ['timestamp']},
        ),
        migrations.AlterField(
            model_name='editorialcommunication',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='editorial_communications', to='submissions.Submission'),
        ),
    ]
