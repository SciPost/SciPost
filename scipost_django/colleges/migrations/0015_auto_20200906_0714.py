# Generated by Django 2.2.11 on 2020-09-06 05:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("ontology", "0007_Branch_Field_Specialty"),
        ("colleges", "0014_auto_20190419_1150"),
    ]

    operations = [
        migrations.CreateModel(
            name="College",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Official name of the College (default: name of the discipline)",
                        max_length=256,
                        unique=True,
                    ),
                ),
                ("order", models.PositiveSmallIntegerField()),
                (
                    "acad_field",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="colleges",
                        to="ontology.AcademicField",
                    ),
                ),
            ],
            options={
                "ordering": ["acad_field", "order"],
            },
        ),
        migrations.AddConstraint(
            model_name="college",
            constraint=models.UniqueConstraint(
                fields=("name", "acad_field"), name="college_unique_name_acad_field"
            ),
        ),
        migrations.AddConstraint(
            model_name="college",
            constraint=models.UniqueConstraint(
                fields=("acad_field", "order"), name="college_unique_acad_field_order"
            ),
        ),
    ]
