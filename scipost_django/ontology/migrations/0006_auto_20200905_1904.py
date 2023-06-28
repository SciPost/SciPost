# Generated by Django 2.2.11 on 2020-09-05 17:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("ontology", "0005_auto_20181028_2038"),
    ]

    operations = [
        migrations.CreateModel(
            name="AcademicField",
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
                ("name", models.CharField(max_length=128)),
                ("slug", models.SlugField(allow_unicode=True, unique=True)),
                ("order", models.PositiveSmallIntegerField()),
            ],
            options={
                "ordering": ["branch", "order"],
            },
        ),
        migrations.CreateModel(
            name="Branch",
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
                ("name", models.CharField(max_length=128)),
                ("slug", models.SlugField(allow_unicode=True, unique=True)),
                ("order", models.PositiveSmallIntegerField(unique=True)),
            ],
            options={
                "verbose_name_plural": "branches",
                "ordering": ["order"],
            },
        ),
        migrations.CreateModel(
            name="Specialty",
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
                ("name", models.CharField(max_length=128)),
                ("slug", models.SlugField(allow_unicode=True, unique=True)),
                ("order", models.PositiveSmallIntegerField()),
                (
                    "acad_field",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="specialties",
                        to="ontology.AcademicField",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "specialties",
                "ordering": ["acad_field", "order"],
            },
        ),
        migrations.AddField(
            model_name="academicfield",
            name="branch",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="academic_fields",
                to="ontology.Branch",
            ),
        ),
        migrations.AddConstraint(
            model_name="specialty",
            constraint=models.UniqueConstraint(
                fields=("acad_field", "order"), name="unique_acad_field_order"
            ),
        ),
        migrations.AddConstraint(
            model_name="academicfield",
            constraint=models.UniqueConstraint(
                fields=("branch", "order"), name="unique_branch_order"
            ),
        ),
    ]
