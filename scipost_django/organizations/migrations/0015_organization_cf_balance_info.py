# Generated by Django 3.2.12 on 2022-02-20 15:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0014_auto_20220220_0946'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='cf_balance_info',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
    ]