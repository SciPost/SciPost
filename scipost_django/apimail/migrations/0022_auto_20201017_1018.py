# Generated by Django 2.2.16 on 2020-10-17 08:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("apimail", "0021_auto_20201017_1016"),
    ]

    operations = [
        migrations.AlterField(
            model_name="emailaccount",
            name="domain",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="email_accounts",
                to="apimail.Domain",
            ),
        ),
    ]
