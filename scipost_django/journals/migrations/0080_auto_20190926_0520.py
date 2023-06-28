# Generated by Django 2.1.8 on 2019-09-26 03:20

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0079_auto_20190925_1450"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="journal",
            options={"ordering": ["discipline", "list_order"]},
        ),
        migrations.AddField(
            model_name="journal",
            name="list_order",
            field=models.PositiveSmallIntegerField(default=100),
        ),
    ]
