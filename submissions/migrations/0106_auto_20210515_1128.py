# Generated by Django 2.2.16 on 2021-05-15 09:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0105_populate_osf_preprint_servers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='refereeinvitation',
            name='date_invited',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
