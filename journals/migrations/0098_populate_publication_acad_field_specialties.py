# Generated by Django 2.2.16 on 2020-09-26 20:24

from django.db import migrations
from django.utils.text import slugify


def populate_acad_field_specialty(apps, schema_editor):
    Publication = apps.get_model('journals.Publication')
    AcademicField = apps.get_model('ontology', 'AcademicField')
    Specialty = apps.get_model('ontology', 'Specialty')

    for p in Publication.objects.all():
        p.acad_field = AcademicField.objects.get(slug=p.discipline)
        p.specialties.add(
            Specialty.objects.get(slug=slugify(p.subject_area.replace(':', '-'))))
        if p.secondary_areas:
            for sa in p.secondary_areas:
                p.specialties.add(
                    Specialty.objects.get(slug=slugify(sa.replace(':', '-'))))
        p.save()


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0097_auto_20200926_2224'),
    ]

    operations = [
        migrations.RunPython(populate_acad_field_specialty,
                             reverse_code=migrations.RunPython.noop),
    ]
