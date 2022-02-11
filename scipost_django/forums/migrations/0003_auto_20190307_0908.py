# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-03-07 08:08
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("forums", "0002_auto_20190306_0807"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="forum",
            options={
                "ordering": ["name"],
                "permissions": [
                    ("can_view_forum", "Can view Forum"),
                    ("can_post_to_forum", "Can add Post to Forum"),
                ],
            },
        ),
    ]
