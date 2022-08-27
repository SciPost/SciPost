# Generated by Django 3.2.14 on 2022-08-27 04:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0018_periodicreport_periodicreporttype'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subsidy',
            name='status',
            field=models.CharField(choices=[('promised', 'promised'), ('invoiced', 'invoiced'), ('received', 'received'), ('withdrawn', 'withdrawn')], max_length=32),
        ),
    ]
