# Generated by Django 3.2.12 on 2022-02-20 20:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0016_organization_cf_expenditure_for_publication'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='cf_associated_publication_ids',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
    ]
