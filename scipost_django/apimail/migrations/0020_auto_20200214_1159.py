# Generated by Django 2.1.8 on 2020-02-14 10:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("apimail", "0019_auto_20200210_0859"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="composedmessage",
            options={"ordering": ["-created_on"]},
        ),
    ]
