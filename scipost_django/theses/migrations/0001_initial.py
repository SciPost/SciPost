# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-29 13:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("scipost", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ThesisLink",
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
                ("vetted", models.BooleanField(default=False)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("MA", "Master's"),
                            ("PhD", "Ph.D."),
                            ("Hab", "Habilitation"),
                        ],
                        max_length=3,
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
                    ),
                ),
                ("open_for_commenting", models.BooleanField(default=True)),
                ("title", models.CharField(max_length=300, verbose_name="title")),
                ("pub_link", models.URLField(verbose_name="URL (external repository)")),
                ("author", models.CharField(max_length=1000)),
                ("supervisor", models.CharField(max_length=1000)),
                (
                    "institution",
                    models.CharField(
                        max_length=300, verbose_name="degree granting institution"
                    ),
                ),
                (
                    "defense_date",
                    models.DateField(verbose_name="date of thesis defense"),
                ),
                (
                    "abstract",
                    models.TextField(verbose_name="abstract, outline or summary"),
                ),
                (
                    "latest_activity",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "author_as_cont",
                    models.ManyToManyField(
                        blank=True, related_name="theses", to="scipost.Contributor"
                    ),
                ),
                (
                    "author_claims",
                    models.ManyToManyField(
                        blank=True,
                        related_name="claimed_theses",
                        to="scipost.Contributor",
                    ),
                ),
                (
                    "author_false_claims",
                    models.ManyToManyField(
                        blank=True,
                        related_name="false_claimed_theses",
                        to="scipost.Contributor",
                    ),
                ),
                (
                    "requested_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="requested_theses",
                        to="scipost.Contributor",
                    ),
                ),
                (
                    "supervisor_as_cont",
                    models.ManyToManyField(
                        blank=True,
                        related_name="supervised_theses",
                        to="scipost.Contributor",
                        verbose_name="supervisor(s)",
                    ),
                ),
                (
                    "vetted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="scipost.Contributor",
                    ),
                ),
            ],
        ),
    ]
