# Generated by Django 4.2.18 on 2025-02-12 13:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0167_alter_refereeindication_unique_together_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eicrecommendation',
            name='remarks_for_editorial_college',
            field=models.TextField(blank=True, verbose_name='Remarks for the Editorial College'),
        ),
    ]
