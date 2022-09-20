# Generated by Django 3.2.14 on 2022-08-27 02:58

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import finances.models


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0017_alter_subsidy_renewable'),
    ]

    operations = [
        migrations.CreateModel(
            name='PeriodicReportType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='PeriodicReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_file', models.FileField(max_length=256, upload_to=finances.models.periodic_report_upload_path)),
                ('created_on', models.DateTimeField(default=django.utils.timezone.now)),
                ('for_year', models.PositiveSmallIntegerField()),
                ('_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='finances.periodicreporttype')),
            ],
        ),
    ]
