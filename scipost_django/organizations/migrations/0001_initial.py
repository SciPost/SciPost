# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-22 11:21
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django_countries.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Organization",
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
                    "orgtype",
                    models.CharField(
                        choices=[
                            ("ResearchRnstitute", "Research Institute"),
                            (
                                "InternationalFundingAgency",
                                "International Funding Agency",
                            ),
                            ("NationalFundingAgency", "National Funding Agency"),
                            ("FundingAgencyInitiative", "Funding Agency Initiative"),
                            ("NationalLaboratory", "National Laboratory"),
                            ("NationalLibrary", "National Library"),
                            ("NationalAcademy", "National Academy"),
                            ("UniversityLibrary", "University (and its Library)"),
                            ("ResearchLibrary", "Research Library"),
                            ("ProfessionalSociety", "Professional Society"),
                            ("InternationalConsortium", "International Consortium"),
                            ("NationalConsortium", "National Consortium"),
                            ("Foundation", "Foundation"),
                            ("GovernmentInternational", "Government (international)"),
                            ("GovernmentNational", "Government (national)"),
                            ("GovernmentProvincial", "Government (provincial)"),
                            ("GovernmentRegional", "Government (regional)"),
                            ("GovernmentMunicipal", "Government (municipal)"),
                            ("GovernmentalMinistry", "Governmental Ministry"),
                            ("GovernmentalOffice", "Governmental Office"),
                            ("BusinessCorporation", "Business Corporation"),
                            ("IndividualBenefactor", "Individual Benefactor"),
                            ("PrivateBenefactor", "Private Benefactor"),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Active", "Active"),
                            ("Superseded", "Superseded"),
                            ("Obsolete", "Obsolete"),
                        ],
                        default="Active",
                        max_length=32,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Western version of name", max_length=256
                    ),
                ),
                (
                    "name_original",
                    models.CharField(
                        blank=True,
                        help_text="Name (in original language)",
                        max_length=256,
                    ),
                ),
                (
                    "acronym",
                    models.CharField(
                        blank=True, help_text="Acronym or short name", max_length=64
                    ),
                ),
                ("country", django_countries.fields.CountryField(max_length=2)),
                ("address", models.TextField(blank=True)),
                (
                    "logo",
                    models.ImageField(blank=True, upload_to="organizations/logos/"),
                ),
                (
                    "css_class",
                    models.CharField(
                        blank=True,
                        max_length=256,
                        verbose_name="Additional logo CSS class",
                    ),
                ),
                (
                    "grid_json",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        blank=True, default={}, null=True
                    ),
                ),
                (
                    "crossref_json",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        blank=True, default={}, null=True
                    ),
                ),
                (
                    "cf_nr_associated_publications",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="NB: nr_associated_publications is a calculated field. Do not modify.",
                        null=True,
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="children",
                        to="organizations.Organization",
                    ),
                ),
                (
                    "superseded_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="organizations.Organization",
                    ),
                ),
            ],
            options={
                "ordering": ["country", "name"],
            },
        ),
    ]
