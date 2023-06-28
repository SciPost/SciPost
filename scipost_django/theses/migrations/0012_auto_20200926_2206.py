# Generated by Django 2.2.16 on 2020-09-26 20:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("ontology", "0007_Branch_Field_Specialty"),
        ("theses", "0011_auto_20191017_0949"),
    ]

    operations = [
        migrations.AddField(
            model_name="thesislink",
            name="acad_field",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="theses",
                to="ontology.AcademicField",
            ),
        ),
        migrations.AddField(
            model_name="thesislink",
            name="specialties",
            field=models.ManyToManyField(
                blank=True, related_name="theses", to="ontology.Specialty"
            ),
        ),
        migrations.AddField(
            model_name="thesislink",
            name="topics",
            field=models.ManyToManyField(blank=True, to="ontology.Topic"),
        ),
    ]
