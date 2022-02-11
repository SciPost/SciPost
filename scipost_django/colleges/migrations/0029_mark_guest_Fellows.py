# Generated by Django 2.2.16 on 2021-03-25 20:20

from django.db import migrations


def mark_guest_Fellows(apps, schema_editor):
    Fellowship = apps.get_model("colleges.Fellowship")
    for f in Fellowship.objects.all():
        if f.guest:
            Fellowship.objects.filter(pk=f.id).update(status="guest")


class Migration(migrations.Migration):

    dependencies = [
        ("colleges", "0028_fellowship_status"),
    ]

    operations = [
        migrations.RunPython(
            mark_guest_Fellows, reverse_code=migrations.RunPython.noop
        ),
    ]
