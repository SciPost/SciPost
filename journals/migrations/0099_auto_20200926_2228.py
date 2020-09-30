# Generated by Django 2.2.16 on 2020-09-26 20:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0098_populate_publication_acad_field_specialties'),
    ]

    operations = [
        migrations.AlterField(
            model_name='publication',
            name='acad_field',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='publications', to='ontology.AcademicField'),
        ),
        migrations.AlterField(
            model_name='publication',
            name='specialties',
            field=models.ManyToManyField(related_name='publications', to='ontology.Specialty'),
        ),
    ]
