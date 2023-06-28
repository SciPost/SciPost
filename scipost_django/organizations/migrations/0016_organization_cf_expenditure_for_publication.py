# Generated by Django 3.2.12 on 2022-02-20 18:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0015_organization_cf_balance_info"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="cf_expenditure_for_publication",
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
    ]
