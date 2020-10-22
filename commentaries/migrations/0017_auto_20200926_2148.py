# Generated by Django 2.2.16 on 2020-09-26 19:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('commentaries', '0016_populate_commentary_acad_field_specialties'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commentary',
            name='acad_field',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='theses', to='ontology.AcademicField'),
        ),
        migrations.AlterField(
            model_name='commentary',
            name='specialties',
            field=models.ManyToManyField(related_name='theses', to='ontology.Specialty'),
        ),
    ]