# Generated by Django 3.2.18 on 2024-03-12 19:36

from django.db import migrations, models
import finances.models
import scipost.storage


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0030_auto_20240312_1822'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subsidyattachment',
            name='attachment',
            field=models.FileField(max_length=256, storage=scipost.storage.SecureFileStorage(), upload_to=finances.models.subsidy_attachment_path),
        ),
    ]
