# Generated by Django 2.2.16 on 2020-09-27 14:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0032_populate_profile_acad_field_specialties'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='discipline',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='expertises',
        ),
    ]
