# Generated by Django 2.1.8 on 2019-09-11 03:47

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0068_auto_20190911_0544"),
    ]

    operations = [
        migrations.AlterField(
            model_name="issue",
            name="number",
            field=models.PositiveIntegerField(),
        ),
    ]
