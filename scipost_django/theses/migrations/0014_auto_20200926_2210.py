# Generated by Django 2.2.16 on 2020-09-26 20:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("theses", "0013_populate_thesislink_acad_field_specialties"),
    ]

    operations = [
        migrations.AlterField(
            model_name="thesislink",
            name="acad_field",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="theses",
                to="ontology.AcademicField",
            ),
        ),
        migrations.AlterField(
            model_name="thesislink",
            name="specialties",
            field=models.ManyToManyField(
                related_name="theses", to="ontology.Specialty"
            ),
        ),
    ]
