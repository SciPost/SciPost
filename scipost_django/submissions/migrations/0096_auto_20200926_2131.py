# Generated by Django 2.2.16 on 2020-09-26 19:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0095_populate_submission_acad_field_specialties"),
    ]

    operations = [
        migrations.AlterField(
            model_name="submission",
            name="acad_field",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="submissions",
                to="ontology.AcademicField",
            ),
        ),
        migrations.AlterField(
            model_name="submission",
            name="specialties",
            field=models.ManyToManyField(
                related_name="submissions", to="ontology.Specialty"
            ),
        ),
    ]
