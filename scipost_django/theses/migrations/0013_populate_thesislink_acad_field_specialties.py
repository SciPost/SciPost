# Generated by Django 2.2.16 on 2020-09-26 20:06

from django.db import migrations
from django.utils.text import slugify


def populate_acad_field_specialty(apps, schema_editor):
    ThesisLink = apps.get_model("theses.ThesisLink")
    AcademicField = apps.get_model("ontology", "AcademicField")
    Specialty = apps.get_model("ontology", "Specialty")

    for t in ThesisLink.objects.all():
        t.acad_field = AcademicField.objects.get(slug=t.discipline)
        t.specialties.add(
            Specialty.objects.get(slug=slugify(t.subject_area.replace(":", "-")))
        )
        t.save()


class Migration(migrations.Migration):
    dependencies = [
        ("theses", "0012_auto_20200926_2206"),
    ]

    operations = [
        migrations.RunPython(
            populate_acad_field_specialty, reverse_code=migrations.RunPython.noop
        ),
    ]
