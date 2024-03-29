# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-02-20 15:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("mails", "0005_auto_20181217_1051"),
    ]

    operations = [
        migrations.CreateModel(
            name="MailLogRelation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=254)),
                ("value", models.CharField(blank=True, max_length=254)),
                ("object_id", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "content_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.ContentType",
                    ),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name="maillog",
            name="content_type",
        ),
        migrations.RemoveField(
            model_name="maillog",
            name="object_id",
        ),
        migrations.AddField(
            model_name="maillogrelation",
            name="mail",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="context",
                to="mails.MailLog",
            ),
        ),
    ]
