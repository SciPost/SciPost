# Generated by Django 4.2.15 on 2024-10-08 15:25

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0022_contactperson_date_deprecated_contactperson_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contactperson",
            name="role",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]