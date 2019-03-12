# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-03-12 13:44
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0008_alter_user_username_max_length'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Queue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('slug', models.SlugField(allow_unicode=True)),
                ('description', models.TextField()),
                ('managing_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='managed_queues', to='auth.Group')),
                ('parent_queue', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='helpdesk.Queue')),
                ('response_groups', models.ManyToManyField(to='auth.Group')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(help_text='You can use ReStructuredText, see a <a href="https://devguide.python.org/documenting/#restructuredtext-primer" target="_blank">primer on python.org</a>')),
                ('publicly_visible', models.BooleanField(default=False, help_text='Do you agree with this Ticket being made publicly visible (and appearing in our public Knowledge Base)?')),
                ('defined_on', models.DateTimeField(default=django.utils.timezone.now)),
                ('priority', models.CharField(choices=[('urgent', 'Urgent (immediate handling needed)'), ('high', 'High (handle as soon as possible)'), ('medium', 'Medium (handle soon)'), ('low', 'Low (handle when available)')], max_length=32)),
                ('deadline', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('unassigned', 'Unassigned'), ('assigned', 'Assigned'), ('resolved', 'Resolved'), ('closed', 'Closed')], max_length=32)),
                ('concerning_object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_tickets', to=settings.AUTH_USER_MODEL)),
                ('concerning_object_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
                ('defined_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('queue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='helpdesk.Queue')),
            ],
            options={
                'ordering': ['queue', 'priority'],
            },
        ),
    ]
