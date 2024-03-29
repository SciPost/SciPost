# Generated by Django 2.2.16 on 2020-09-26 19:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("ontology", "0007_Branch_Field_Specialty"),
        ("submissions", "0093_auto_20200915_1359"),
    ]

    operations = [
        migrations.AddField(
            model_name="submission",
            name="acad_field",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="submissions",
                to="ontology.AcademicField",
            ),
        ),
        migrations.AddField(
            model_name="submission",
            name="specialties",
            field=models.ManyToManyField(
                blank=True, related_name="submissions", to="ontology.Specialty"
            ),
        ),
    ]
