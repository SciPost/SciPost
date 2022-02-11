# Generated by Django 2.2.11 on 2020-09-06 12:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("colleges", "0018_fellowship_set_college"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fellowship",
            name="college",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="fellowships",
                to="colleges.College",
            ),
        ),
    ]
