# Generated by Django 2.2.16 on 2021-05-02 08:40

from django.db import migrations


def populate_figshare_preprint_servers(apps, schema_editor):
    PreprintServer = apps.get_model("submissions.PreprintServer")
    AcademicField = apps.get_model("ontology", "AcademicField")

    figshare, created = PreprintServer.objects.get_or_create(
        name="Figshare", url="https://figshare.com"
    )

    chemrxiv, created = PreprintServer.objects.get_or_create(
        name="ChemRxiv", url="https://chemrxiv.org", served_by=figshare
    )
    if created:
        chemrxiv.acad_fields.add(AcademicField.objects.get(name="Chemistry"))
        chemrxiv.save()

    techrxiv, created = PreprintServer.objects.get_or_create(
        name="TechRxiv", url="https://www.techrxiv.org", served_by=figshare
    )
    if created:
        techrxiv.acad_fields.add(AcademicField.objects.get(name="Computer Science"))
        techrxiv.save()

    advance, created = PreprintServer.objects.get_or_create(
        name="Advance", url="https://advance.sagepub.com/", served_by=figshare
    )
    if created:
        advance.acad_fields.add(AcademicField.objects.get(name="Political Science"))
        advance.save()


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0103_preprintserver_served_by"),
    ]

    operations = [
        migrations.RunPython(
            populate_figshare_preprint_servers, reverse_code=migrations.RunPython.noop
        ),
    ]
