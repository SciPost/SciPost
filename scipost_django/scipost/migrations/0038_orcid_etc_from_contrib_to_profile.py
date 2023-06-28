# Generated by Django 2.2.16 on 2020-09-30 02:35

from django.db import migrations


def transfer_from_contributor_to_profile(apps, schema_editor):
    Contributor = apps.get_model("scipost.Contributor")
    Profile = apps.get_model("profiles.Profile")

    for c in Contributor.objects.all():
        if c.profile:
            if c.orcid_id:
                Profile.objects.filter(pk=c.profile.id).update(orcid_id=c.orcid_id)
            Profile.objects.filter(pk=c.profile.id).update(title=c.title)
            if c.personalwebpage:
                Profile.objects.filter(pk=c.profile.id).update(
                    webpage=c.personalwebpage
                )
            if not c.accepts_SciPost_emails:
                Profile.objects.filter(pk=c.profile.id).update(
                    accepts_SciPost_emails=False
                )


class Migration(migrations.Migration):
    dependencies = [
        ("scipost", "0037_auto_20200929_1234"),
    ]

    operations = [
        migrations.RunPython(
            transfer_from_contributor_to_profile, reverse_code=migrations.RunPython.noop
        ),
    ]
