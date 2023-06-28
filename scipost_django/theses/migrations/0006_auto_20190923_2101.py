# Generated by Django 2.1.8 on 2019-09-23 19:01

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("theses", "0005_remove_thesislink_domain"),
    ]

    operations = [
        migrations.AlterField(
            model_name="thesislink",
            name="discipline",
            field=models.CharField(
                choices=[
                    (
                        "Multidisciplinary",
                        (("multidisciplinary", "Multidisciplinary (any combination)"),),
                    ),
                    (
                        "Formal Sciences",
                        (
                            ("mathematics", "Mathematics"),
                            ("computerscience", "Computer Science"),
                        ),
                    ),
                    (
                        "Natural Sciences",
                        (
                            ("physics", "Physics"),
                            ("astronomy", "Astronomy"),
                            ("astrophysics", "Astrophysics"),
                            ("biology", "Biology"),
                            ("chemistry", "Chemistry"),
                            (
                                "earthscienceEarth and Environmental Sciences",
                                "Earth and Environmental Sciences",
                            ),
                        ),
                    ),
                    (
                        "Engineering",
                        (
                            ("civileng", "Civil Engineering"),
                            ("electricaleng", "Electrical Engineering"),
                            ("mechanicaleng", "Mechanical Engineering"),
                            ("chemicaleng", "Chemical Engineering"),
                            ("materialseng", "Materials Engineering"),
                            ("medicaleng", "Medical Engineering"),
                            ("environmentaleng", "Environmental Engineering"),
                            ("industrialeng", "Industrial Engineering"),
                        ),
                    ),
                    (
                        "Medical Sciences",
                        (
                            ("medicine", "Basic Medicine"),
                            ("clinicalClinical Medicine", "Clinical Medicine"),
                            ("healthHealth Sciences", "Health Sciences"),
                        ),
                    ),
                    (
                        "Agricultural Sciences",
                        (
                            (
                                "agriculturalAgriculture, Forestry and Fisheries",
                                "Agriculture, Forestry and Fisheries",
                            ),
                            ("veterinary", "Veterinary Science"),
                        ),
                    ),
                    (
                        "Social Sciences",
                        (
                            ("economics", "Economics"),
                            ("geography", "Geography"),
                            ("law", "Law"),
                            ("media", "Media and Communications"),
                            ("pedagogy", "Pedagogy and Educational Sciences"),
                            ("politicalscience", "Political Science"),
                            ("psychology", "Psychology"),
                            ("sociology", "Sociology"),
                        ),
                    ),
                    (
                        "Humanities",
                        (
                            (
                                "artArt (arts, history or arts, performing arts, music)",
                                "Art (arts, history or arts, performing arts, music)",
                            ),
                            ("historyHistory and Archeology", "History and Archeology"),
                            (
                                "literatureLanguage and Literature",
                                "Language and Literature",
                            ),
                            (
                                "philosophyPhilosophy, Ethics and Religion",
                                "Philosophy, Ethics and Religion",
                            ),
                        ),
                    ),
                ],
                default="physics",
                max_length=20,
            ),
        ),
    ]
