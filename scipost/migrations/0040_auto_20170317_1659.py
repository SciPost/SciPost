# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-03-17 15:59
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0039_auto_20170306_0804'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='arc',
            name='added_by',
        ),
        migrations.RemoveField(
            model_name='arc',
            name='graph',
        ),
        migrations.RemoveField(
            model_name='arc',
            name='source',
        ),
        migrations.RemoveField(
            model_name='arc',
            name='target',
        ),
        migrations.RemoveField(
            model_name='graph',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='graph',
            name='teams_with_access',
        ),
        migrations.RemoveField(
            model_name='list',
            name='commentaries',
        ),
        migrations.RemoveField(
            model_name='list',
            name='comments',
        ),
        migrations.RemoveField(
            model_name='list',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='list',
            name='submissions',
        ),
        migrations.RemoveField(
            model_name='list',
            name='teams_with_access',
        ),
        migrations.RemoveField(
            model_name='list',
            name='thesislinks',
        ),
        migrations.RemoveField(
            model_name='node',
            name='added_by',
        ),
        migrations.RemoveField(
            model_name='node',
            name='commentaries',
        ),
        migrations.RemoveField(
            model_name='node',
            name='graph',
        ),
        migrations.RemoveField(
            model_name='node',
            name='submissions',
        ),
        migrations.RemoveField(
            model_name='node',
            name='thesislinks',
        ),
        migrations.RemoveField(
            model_name='team',
            name='leader',
        ),
        migrations.RemoveField(
            model_name='team',
            name='members',
        ),
        migrations.DeleteModel(
            name='Arc',
        ),
        migrations.DeleteModel(
            name='Graph',
        ),
        migrations.DeleteModel(
            name='List',
        ),
        migrations.DeleteModel(
            name='Node',
        ),
        migrations.DeleteModel(
            name='Team',
        ),
    ]
