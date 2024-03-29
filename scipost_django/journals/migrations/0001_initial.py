# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-29 13:35
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import scipost.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Deposit",
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
                ("timestamp", models.CharField(default="", max_length=40)),
                ("doi_batch_id", models.CharField(default="", max_length=40)),
                ("metadata_xml", models.TextField(blank=True, null=True)),
                (
                    "metadata_xml_file",
                    models.FileField(
                        blank=True, max_length=512, null=True, upload_to=""
                    ),
                ),
                ("deposition_date", models.DateTimeField(blank=True, null=True)),
                ("response_text", models.TextField(blank=True, null=True)),
                ("deposit_successful", models.NullBooleanField(default=None)),
            ],
            options={
                "ordering": ["-timestamp"],
            },
        ),
        migrations.CreateModel(
            name="DOAJDeposit",
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
                ("timestamp", models.CharField(default="", max_length=40)),
                ("metadata_DOAJ", django.contrib.postgres.fields.jsonb.JSONField()),
                (
                    "metadata_DOAJ_file",
                    models.FileField(
                        blank=True, max_length=512, null=True, upload_to=""
                    ),
                ),
                ("deposition_date", models.DateTimeField(blank=True, null=True)),
                ("response_text", models.TextField(blank=True, null=True)),
                ("deposit_successful", models.NullBooleanField(default=None)),
            ],
            options={
                "verbose_name": "DOAJ deposit",
            },
        ),
        migrations.CreateModel(
            name="GenericDOIDeposit",
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
                ("object_id", models.PositiveIntegerField()),
                ("timestamp", models.CharField(default="", max_length=40)),
                ("doi_batch_id", models.CharField(default="", max_length=40)),
                ("metadata_xml", models.TextField(blank=True, null=True)),
                ("deposition_date", models.DateTimeField(blank=True, null=True)),
                ("response", models.TextField(blank=True, null=True)),
                ("deposit_successful", models.NullBooleanField(default=None)),
            ],
            options={
                "ordering": ["-timestamp"],
            },
        ),
        migrations.CreateModel(
            name="Issue",
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
                ("number", models.PositiveSmallIntegerField()),
                ("start_date", models.DateField(default=django.utils.timezone.now)),
                ("until_date", models.DateField(default=django.utils.timezone.now)),
                (
                    "status",
                    models.CharField(
                        choices=[("draft", "Draft"), ("published", "Published")],
                        default="published",
                        max_length=20,
                    ),
                ),
                (
                    "doi_label",
                    models.CharField(
                        db_index=True,
                        max_length=200,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^[a-zA-Z]+.[0-9]+.[0-9]+$",
                                "Only valid DOI expressions are allowed ([a-zA-Z]+.[0-9]+.[0-9]+).",
                            )
                        ],
                    ),
                ),
                ("path", models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name="Journal",
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
                        choices=[
                            ("SciPostPhys", "SciPost Physics"),
                            ("SciPostPhysLectNotes", "SciPost Physics Lecture Notes"),
                            ("SciPostPhysProc", "SciPost Physics Proceedings"),
                            ("SciPostPhysSel", "SciPost Physics Select"),
                        ],
                        max_length=100,
                        unique=True,
                    ),
                ),
                (
                    "doi_label",
                    models.CharField(
                        db_index=True,
                        max_length=200,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^[a-zA-Z]+$",
                                "Only valid DOI expressions are allowed ([a-zA-Z]+).",
                            )
                        ],
                    ),
                ),
                (
                    "issn",
                    models.CharField(blank=True, default="2542-4653", max_length=16),
                ),
                ("active", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="Publication",
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
                ("paper_nr", models.PositiveSmallIntegerField()),
                ("title", models.CharField(max_length=300)),
                (
                    "author_list",
                    models.CharField(max_length=1000, verbose_name="author list"),
                ),
                ("abstract", models.TextField()),
                (
                    "pdf_file",
                    models.FileField(
                        max_length=200, upload_to="UPLOADS/PUBLICATIONS/%Y/%m/"
                    ),
                ),
                (
                    "discipline",
                    models.CharField(
                        choices=[
                            ("physics", "Physics"),
                            ("astrophysics", "Astrophysics"),
                            ("mathematics", "Mathematics"),
                            ("computerscience", "Computer Science"),
                        ],
                        default="physics",
                        max_length=20,
                    ),
                ),
                (
                    "domain",
                    models.CharField(
                        choices=[
                            ("E", "Experimental"),
                            ("T", "Theoretical"),
                            ("C", "Computational"),
                            ("ET", "Exp. & Theor."),
                            ("EC", "Exp. & Comp."),
                            ("TC", "Theor. & Comp."),
                            ("ETC", "Exp., Theor. & Comp."),
                        ],
                        max_length=3,
                    ),
                ),
                (
                    "subject_area",
                    models.CharField(
                        choices=[
                            (
                                "Physics",
                                (
                                    (
                                        "Phys:AE",
                                        "Atomic, Molecular and Optical Physics - Experiment",
                                    ),
                                    (
                                        "Phys:AT",
                                        "Atomic, Molecular and Optical Physics - Theory",
                                    ),
                                    ("Phys:BI", "Biophysics"),
                                    (
                                        "Phys:CE",
                                        "Condensed Matter Physics - Experiment",
                                    ),
                                    ("Phys:CT", "Condensed Matter Physics - Theory"),
                                    ("Phys:FD", "Fluid Dynamics"),
                                    (
                                        "Phys:GR",
                                        "Gravitation, Cosmology and Astroparticle Physics",
                                    ),
                                    ("Phys:HE", "High-Energy Physics - Experiment"),
                                    ("Phys:HT", "High-Energy Physics - Theory"),
                                    ("Phys:HP", "High-Energy Physics - Phenomenology"),
                                    ("Phys:MP", "Mathematical Physics"),
                                    ("Phys:NE", "Nuclear Physics - Experiment"),
                                    ("Phys:NT", "Nuclear Physics - Theory"),
                                    ("Phys:QP", "Quantum Physics"),
                                    ("Phys:SM", "Statistical and Soft Matter Physics"),
                                ),
                            ),
                            (
                                "Astrophysics",
                                (
                                    ("Astro:GA", "Astrophysics of Galaxies"),
                                    (
                                        "Astro:CO",
                                        "Cosmology and Nongalactic Astrophysics",
                                    ),
                                    ("Astro:EP", "Earth and Planetary Astrophysics"),
                                    ("Astro:HE", "High Energy Astrophysical Phenomena"),
                                    (
                                        "Astro:IM",
                                        "Instrumentation and Methods for Astrophysics",
                                    ),
                                    ("Astro:SR", "Solar and Stellar Astrophysics"),
                                ),
                            ),
                            (
                                "Mathematics",
                                (
                                    ("Math:AG", "Algebraic Geometry"),
                                    ("Math:AT", "Algebraic Topology"),
                                    ("Math:AP", "Analysis of PDEs"),
                                    ("Math:CT", "Category Theory"),
                                    ("Math:CA", "Classical Analysis and ODEs"),
                                    ("Math:CO", "Combinatorics"),
                                    ("Math:AC", "Commutative Algebra"),
                                    ("Math:CV", "Complex Variables"),
                                    ("Math:DG", "Differential Geometry"),
                                    ("Math:DS", "Dynamical Systems"),
                                    ("Math:FA", "Functional Analysis"),
                                    ("Math:GM", "General Mathematics"),
                                    ("Math:GN", "General Topology"),
                                    ("Math:GT", "Geometric Topology"),
                                    ("Math:GR", "Group Theory"),
                                    ("Math:HO", "History and Overview"),
                                    ("Math:IT", "Information Theory"),
                                    ("Math:KT", "K-Theory and Homology"),
                                    ("Math:LO", "Logic"),
                                    ("Math:MP", "Mathematical Physics"),
                                    ("Math:MG", "Metric Geometry"),
                                    ("Math:NT", "Number Theory"),
                                    ("Math:NA", "Numerical Analysis"),
                                    ("Math:OA", "Operator Algebras"),
                                    ("Math:OC", "Optimization and Control"),
                                    ("Math:PR", "Probability"),
                                    ("Math:QA", "Quantum Algebra"),
                                    ("Math:RT", "Representation Theory"),
                                    ("Math:RA", "Rings and Algebras"),
                                    ("Math:SP", "Spectral Theory"),
                                    ("Math:ST", "Statistics Theory"),
                                    ("Math:SG", "Symplectic Geometry"),
                                ),
                            ),
                            (
                                "Computer Science",
                                (
                                    ("Comp:AI", "Artificial Intelligence"),
                                    ("Comp:CC", "Computational Complexity"),
                                    (
                                        "Comp:CE",
                                        "Computational Engineering, Finance, and Science",
                                    ),
                                    ("Comp:CG", "Computational Geometry"),
                                    ("Comp:GT", "Computer Science and Game Theory"),
                                    (
                                        "Comp:CV",
                                        "Computer Vision and Pattern Recognition",
                                    ),
                                    ("Comp:CY", "Computers and Society"),
                                    ("Comp:CR", "Cryptography and Security"),
                                    ("Comp:DS", "Data Structures and Algorithms"),
                                    ("Comp:DB", "Databases"),
                                    ("Comp:DL", "Digital Libraries"),
                                    ("Comp:DM", "Discrete Mathematics"),
                                    (
                                        "Comp:DC",
                                        "Distributed, Parallel, and Cluster Computing",
                                    ),
                                    ("Comp:ET", "Emerging Technologies"),
                                    ("Comp:FL", "Formal Languages and Automata Theory"),
                                    ("Comp:GL", "General Literature"),
                                    ("Comp:GR", "Graphics"),
                                    ("Comp:AR", "Hardware Architecture"),
                                    ("Comp:HC", "Human-Computer Interaction"),
                                    ("Comp:IR", "Information Retrieval"),
                                    ("Comp:IT", "Information Theory"),
                                    ("Comp:LG", "Learning"),
                                    ("Comp:LO", "Logic in Computer Science"),
                                    ("Comp:MS", "Mathematical Software"),
                                    ("Comp:MA", "Multiagent Systems"),
                                    ("Comp:MM", "Multimedia"),
                                    ("Comp:NI", "Networking and Internet Architecture"),
                                    ("Comp:NE", "Neural and Evolutionary Computing"),
                                    ("Comp:NA", "Numerical Analysis"),
                                    ("Comp:OS", "Operating Systems"),
                                    ("Comp:OH", "Other Computer Science"),
                                    ("Comp:PF", "Performance"),
                                    ("Comp:PL", "Programming Languages"),
                                    ("Comp:RO", "Robotics"),
                                    ("Comp:SI", "Social and Information Networks"),
                                    ("Comp:SE", "Software Engineering"),
                                    ("Comp:SD", "Sound"),
                                    ("Comp:SC", "Symbolic Computation"),
                                    ("Comp:SY", "Systems and Control"),
                                ),
                            ),
                        ],
                        default="Phys:QP",
                        max_length=10,
                        verbose_name="Primary subject area",
                    ),
                ),
                (
                    "secondary_areas",
                    scipost.fields.ChoiceArrayField(
                        base_field=models.CharField(
                            choices=[
                                (
                                    "Physics",
                                    (
                                        (
                                            "Phys:AE",
                                            "Atomic, Molecular and Optical Physics - Experiment",
                                        ),
                                        (
                                            "Phys:AT",
                                            "Atomic, Molecular and Optical Physics - Theory",
                                        ),
                                        ("Phys:BI", "Biophysics"),
                                        (
                                            "Phys:CE",
                                            "Condensed Matter Physics - Experiment",
                                        ),
                                        (
                                            "Phys:CT",
                                            "Condensed Matter Physics - Theory",
                                        ),
                                        ("Phys:FD", "Fluid Dynamics"),
                                        (
                                            "Phys:GR",
                                            "Gravitation, Cosmology and Astroparticle Physics",
                                        ),
                                        ("Phys:HE", "High-Energy Physics - Experiment"),
                                        ("Phys:HT", "High-Energy Physics - Theory"),
                                        (
                                            "Phys:HP",
                                            "High-Energy Physics - Phenomenology",
                                        ),
                                        ("Phys:MP", "Mathematical Physics"),
                                        ("Phys:NE", "Nuclear Physics - Experiment"),
                                        ("Phys:NT", "Nuclear Physics - Theory"),
                                        ("Phys:QP", "Quantum Physics"),
                                        (
                                            "Phys:SM",
                                            "Statistical and Soft Matter Physics",
                                        ),
                                    ),
                                ),
                                (
                                    "Astrophysics",
                                    (
                                        ("Astro:GA", "Astrophysics of Galaxies"),
                                        (
                                            "Astro:CO",
                                            "Cosmology and Nongalactic Astrophysics",
                                        ),
                                        (
                                            "Astro:EP",
                                            "Earth and Planetary Astrophysics",
                                        ),
                                        (
                                            "Astro:HE",
                                            "High Energy Astrophysical Phenomena",
                                        ),
                                        (
                                            "Astro:IM",
                                            "Instrumentation and Methods for Astrophysics",
                                        ),
                                        ("Astro:SR", "Solar and Stellar Astrophysics"),
                                    ),
                                ),
                                (
                                    "Mathematics",
                                    (
                                        ("Math:AG", "Algebraic Geometry"),
                                        ("Math:AT", "Algebraic Topology"),
                                        ("Math:AP", "Analysis of PDEs"),
                                        ("Math:CT", "Category Theory"),
                                        ("Math:CA", "Classical Analysis and ODEs"),
                                        ("Math:CO", "Combinatorics"),
                                        ("Math:AC", "Commutative Algebra"),
                                        ("Math:CV", "Complex Variables"),
                                        ("Math:DG", "Differential Geometry"),
                                        ("Math:DS", "Dynamical Systems"),
                                        ("Math:FA", "Functional Analysis"),
                                        ("Math:GM", "General Mathematics"),
                                        ("Math:GN", "General Topology"),
                                        ("Math:GT", "Geometric Topology"),
                                        ("Math:GR", "Group Theory"),
                                        ("Math:HO", "History and Overview"),
                                        ("Math:IT", "Information Theory"),
                                        ("Math:KT", "K-Theory and Homology"),
                                        ("Math:LO", "Logic"),
                                        ("Math:MP", "Mathematical Physics"),
                                        ("Math:MG", "Metric Geometry"),
                                        ("Math:NT", "Number Theory"),
                                        ("Math:NA", "Numerical Analysis"),
                                        ("Math:OA", "Operator Algebras"),
                                        ("Math:OC", "Optimization and Control"),
                                        ("Math:PR", "Probability"),
                                        ("Math:QA", "Quantum Algebra"),
                                        ("Math:RT", "Representation Theory"),
                                        ("Math:RA", "Rings and Algebras"),
                                        ("Math:SP", "Spectral Theory"),
                                        ("Math:ST", "Statistics Theory"),
                                        ("Math:SG", "Symplectic Geometry"),
                                    ),
                                ),
                                (
                                    "Computer Science",
                                    (
                                        ("Comp:AI", "Artificial Intelligence"),
                                        ("Comp:CC", "Computational Complexity"),
                                        (
                                            "Comp:CE",
                                            "Computational Engineering, Finance, and Science",
                                        ),
                                        ("Comp:CG", "Computational Geometry"),
                                        ("Comp:GT", "Computer Science and Game Theory"),
                                        (
                                            "Comp:CV",
                                            "Computer Vision and Pattern Recognition",
                                        ),
                                        ("Comp:CY", "Computers and Society"),
                                        ("Comp:CR", "Cryptography and Security"),
                                        ("Comp:DS", "Data Structures and Algorithms"),
                                        ("Comp:DB", "Databases"),
                                        ("Comp:DL", "Digital Libraries"),
                                        ("Comp:DM", "Discrete Mathematics"),
                                        (
                                            "Comp:DC",
                                            "Distributed, Parallel, and Cluster Computing",
                                        ),
                                        ("Comp:ET", "Emerging Technologies"),
                                        (
                                            "Comp:FL",
                                            "Formal Languages and Automata Theory",
                                        ),
                                        ("Comp:GL", "General Literature"),
                                        ("Comp:GR", "Graphics"),
                                        ("Comp:AR", "Hardware Architecture"),
                                        ("Comp:HC", "Human-Computer Interaction"),
                                        ("Comp:IR", "Information Retrieval"),
                                        ("Comp:IT", "Information Theory"),
                                        ("Comp:LG", "Learning"),
                                        ("Comp:LO", "Logic in Computer Science"),
                                        ("Comp:MS", "Mathematical Software"),
                                        ("Comp:MA", "Multiagent Systems"),
                                        ("Comp:MM", "Multimedia"),
                                        (
                                            "Comp:NI",
                                            "Networking and Internet Architecture",
                                        ),
                                        (
                                            "Comp:NE",
                                            "Neural and Evolutionary Computing",
                                        ),
                                        ("Comp:NA", "Numerical Analysis"),
                                        ("Comp:OS", "Operating Systems"),
                                        ("Comp:OH", "Other Computer Science"),
                                        ("Comp:PF", "Performance"),
                                        ("Comp:PL", "Programming Languages"),
                                        ("Comp:RO", "Robotics"),
                                        ("Comp:SI", "Social and Information Networks"),
                                        ("Comp:SE", "Software Engineering"),
                                        ("Comp:SD", "Sound"),
                                        ("Comp:SC", "Symbolic Computation"),
                                        ("Comp:SY", "Systems and Control"),
                                    ),
                                ),
                            ],
                            max_length=10,
                        ),
                        blank=True,
                        null=True,
                        size=None,
                    ),
                ),
                (
                    "cc_license",
                    models.CharField(
                        choices=[
                            ("CC BY 4.0", "CC BY (4.0)"),
                            ("CC BY-SA 4.0", "CC BY-SA (4.0)"),
                            ("CC BY-NC 4.0", "CC BY-NC (4.0)"),
                        ],
                        default="CC BY 4.0",
                        max_length=32,
                    ),
                ),
                (
                    "metadata",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        blank=True, default={}, null=True
                    ),
                ),
                ("metadata_xml", models.TextField(blank=True, null=True)),
                (
                    "metadata_DOAJ",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        blank=True, default={}, null=True
                    ),
                ),
                (
                    "doi_label",
                    models.CharField(
                        db_index=True,
                        max_length=200,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^[a-zA-Z]+.[0-9]+.[0-9]+.[0-9]{3,}$",
                                "Only valid DOI expressions are allowed ([a-zA-Z]+.[0-9]+.[0-9]+.[0-9]{3,}).",
                            )
                        ],
                    ),
                ),
                ("BiBTeX_entry", models.TextField(blank=True, null=True)),
                ("doideposit_needs_updating", models.BooleanField(default=False)),
                (
                    "citedby",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        blank=True, default={}, null=True
                    ),
                ),
                ("submission_date", models.DateField(verbose_name="submission date")),
                ("acceptance_date", models.DateField(verbose_name="acceptance date")),
                ("publication_date", models.DateField(verbose_name="publication date")),
                ("latest_citedby_update", models.DateTimeField(blank=True, null=True)),
                ("latest_metadata_update", models.DateTimeField(blank=True, null=True)),
                (
                    "latest_activity",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UnregisteredAuthor",
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
                ("first_name", models.CharField(max_length=100)),
                ("last_name", models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="Volume",
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
                ("number", models.PositiveSmallIntegerField()),
                ("start_date", models.DateField(default=django.utils.timezone.now)),
                ("until_date", models.DateField(default=django.utils.timezone.now)),
                (
                    "doi_label",
                    models.CharField(
                        db_index=True,
                        max_length=200,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^[a-zA-Z]+.[0-9]+$",
                                "Only valid DOI expressions are allowed ([a-zA-Z]+.[0-9]+).",
                            )
                        ],
                    ),
                ),
                (
                    "in_journal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="journals.Journal",
                    ),
                ),
            ],
        ),
    ]
