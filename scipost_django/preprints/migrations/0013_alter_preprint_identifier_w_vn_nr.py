# Generated by Django 3.2.5 on 2021-09-17 07:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("preprints", "0012_auto_20200721_0933"),
    ]

    operations = [
        migrations.AlterField(
            model_name="preprint",
            name="identifier_w_vn_nr",
            field=models.CharField(db_index=True, max_length=128, unique=True),
        ),
    ]
