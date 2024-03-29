# Generated by Django 3.2.12 on 2022-03-14 06:23

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0018_auto_20220223_0737"),
    ]

    operations = [
        migrations.AlterField(
            model_name="organization",
            name="cf_associated_publication_ids",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="NB: calculated field. Do not modify.",
            ),
        ),
        migrations.AlterField(
            model_name="organization",
            name="cf_balance_info",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="NB: calculated field. Do not modify.",
            ),
        ),
        migrations.AlterField(
            model_name="organization",
            name="cf_expenditure_for_publication",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="NB: calculated field. Do not modify.",
            ),
        ),
    ]
