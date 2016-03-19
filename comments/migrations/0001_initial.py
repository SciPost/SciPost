# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-03-19 05:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorReply',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.SmallIntegerField(default=0)),
                ('reply_text', models.TextField(verbose_name='')),
                ('date_submitted', models.DateTimeField(verbose_name='date submitted')),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.SmallIntegerField(default=0)),
                ('anonymous', models.BooleanField(default=False, verbose_name='Publish anonymously')),
                ('is_rem', models.BooleanField(default=False, verbose_name='remark')),
                ('is_que', models.BooleanField(default=False, verbose_name='question')),
                ('is_ans', models.BooleanField(default=False, verbose_name='answer to question')),
                ('is_obj', models.BooleanField(default=False, verbose_name='objection')),
                ('is_rep', models.BooleanField(default=False, verbose_name='reply to objection')),
                ('is_val', models.BooleanField(default=False, verbose_name='validation or rederivation')),
                ('is_lit', models.BooleanField(default=False, verbose_name='pointer to related literature')),
                ('is_sug', models.BooleanField(default=False, verbose_name='suggestion for further work')),
                ('comment_text', models.TextField()),
                ('remarks_for_editors', models.TextField(blank=True, default='', verbose_name='optional remarks for the Editors only')),
                ('date_submitted', models.DateTimeField(verbose_name='date submitted')),
            ],
        ),
    ]
