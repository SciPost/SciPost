# Generated by Django 3.2.18 on 2023-10-06 15:27

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0009_productionstream_on_hold'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productionstream',
            name='opened',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
