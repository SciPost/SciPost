# Generated by Django 2.2.11 on 2020-09-06 05:16

from django.db import migrations

from ontology.models import AcademicField


def populate_colleges(apps, schema_editor):
    AcademicField = apps.get_model('ontology', 'AcademicField')
    College = apps.get_model('colleges.College')

    for af in AcademicField.objects.all():
        college, created = College.objects.get_or_create(
            name=af.name,
            acad_field=af,
            order=1
        )


class Migration(migrations.Migration):

    dependencies = [
        ('colleges', '0015_auto_20200906_0714'),
    ]

    operations = [
        migrations.RunPython(populate_colleges,
                             reverse_code=migrations.RunPython.noop),
    ]
