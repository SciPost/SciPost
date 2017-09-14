# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-14 20:37
from __future__ import unicode_literals

from django.contrib.auth.models import Group, User
from django.db import migrations


def contributor_to_officer(apps, schema_editor):
    # Create ProductionUser for all current Officers
    ProductionUser = apps.get_model('production', 'ProductionUser')
    officers = Group.objects.get(name='Production Officers')
    for user in officers.user_set.all():
        ProductionUser.objects.get_or_create(user__id=user.id)
    print('\n  - Production Officers transfered to ProductionUser')

    # Transfer all Events
    ProductionEvent = apps.get_model('production', 'ProductionEvent')
    for event in ProductionEvent.objects.all():
        user = User.objects.get(contributor__id=event.noted_by_contributor.id)
        event.noted_by.id = user.production_user.id
        event.save()
    print('  - ProductionEvents updated')

    return


def officer_to_contributor(apps, schema_editor):
    # Transfer all Events
    ProductionEvent = apps.get_model('production', 'ProductionEvent')
    for event in ProductionEvent.objects.all():
        user = User.objects.get(production_user__id=event.noted_by.id)
        event.noted_by_contributor.id = user.contributor.id
        event.save()
    print('\n  - ProductionEvents updated')

    return


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0014_productionevent_noted_by'),
    ]

    operations = [
        migrations.RunPython(contributor_to_officer, officer_to_contributor)
    ]
