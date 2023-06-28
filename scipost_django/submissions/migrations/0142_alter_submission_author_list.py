# Generated by Django 3.2.16 on 2023-01-24 10:58

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0141_alter_readiness_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="submission",
            name="author_list",
            field=models.CharField(
                help_text="Please use full first names (we <strong>beg</strong> you!): <em>Abe Cee, Dee Efgee, Haich Idjay Kay</em><br>(not providing full first names makes metadata handling unnecessarily work-intensive for us)",
                max_length=10000,
                verbose_name="author list",
            ),
        ),
    ]
