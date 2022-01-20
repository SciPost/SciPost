# Generated by Django 3.2.5 on 2022-01-20 18:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0035_alter_profile_title'),
        ('series', '0005_series_information'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='expected_authors',
            field=models.ManyToManyField(blank=True, to='profiles.Profile'),
        ),
    ]
