# Generated by Django 2.2.11 on 2020-04-22 14:13

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0081_auto_20191026_1828"),
        ("series", "0002_auto_20191112_0846"),
    ]

    operations = [
        migrations.AddField(
            model_name="collection",
            name="submissions",
            field=models.ManyToManyField(blank=True, to="submissions.Submission"),
        ),
    ]
