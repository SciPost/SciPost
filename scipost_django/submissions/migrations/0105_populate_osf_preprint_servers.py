# Generated by Django 2.2.16 on 2021-05-02 09:12

from django.db import migrations


def populate_osf_preprint_servers(apps, schema_editor):
    PreprintServer = apps.get_model("submissions.PreprintServer")
    AcademicField = apps.get_model("ontology", "AcademicField")

    osfpreprints, created = PreprintServer.objects.get_or_create(
        name="OSFPreprints", url="https://osf.io/preprints/"
    )

    socarxiv, created = PreprintServer.objects.get_or_create(
        name="SocArXiv", url="https://socarxiv.org", served_by=osfpreprints
    )
    if created:
        socarxiv.acad_fields.add(AcademicField.objects.get(name="Political Science"))
        socarxiv.save()


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0104_populate_figshare_preprint_servers"),
    ]

    operations = [
        migrations.RunPython(
            populate_osf_preprint_servers, reverse_code=migrations.RunPython.noop
        ),
    ]
