# Generated by Django 2.2.16 on 2020-09-26 09:55

from django.db import migrations
from django.utils.text import slugify


def populate_acad_field_specialty(apps, schema_editor):
    Profile = apps.get_model("profiles.Profile")
    AcademicField = apps.get_model("ontology", "AcademicField")
    Specialty = apps.get_model("ontology", "Specialty")

    for p in Profile.objects.all():
        p.acad_field = AcademicField.objects.get(slug=p.discipline)
        # Fish out specialties from profile.expertises:
        if p.expertises:
            for e in p.expertises:
                p.specialties.add(
                    Specialty.objects.get(slug=slugify(e.replace(":", "-")))
                )
        # Fish out specialties from profile.contributor.expertises, if contributor exists:
        try:
            if p.contributor.expertises:
                for e in p.contributor.expertises:
                    p.specialties.add(
                        Specialty.objects.get(slug=slugify(e.replace(":", "-")))
                    )
        except (TypeError, Profile.contributor.RelatedObjectDoesNotExist):
            pass
        p.save()


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0031_auto_20200926_1147"),
    ]

    operations = [
        migrations.RunPython(
            populate_acad_field_specialty, reverse_code=migrations.RunPython.noop
        ),
    ]
