# Generated by Django 4.2.10 on 2024-03-20 15:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("finances", "0043_alter_pubfrac_cf_value"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="subsidy",
            name="algorithm",
        ),
        migrations.RemoveField(
            model_name="subsidy",
            name="algorithm_data",
        ),
    ]
