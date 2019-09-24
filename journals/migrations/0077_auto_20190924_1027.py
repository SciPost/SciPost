# Generated by Django 2.1.8 on 2019-09-24 08:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0076_auto_20190923_2101'),
    ]

    operations = [
        migrations.AddField(
            model_name='journal',
            name='acceptance_criteria',
            field=models.TextField(default='[To be filled in; you can use markup]'),
        ),
        migrations.AddField(
            model_name='journal',
            name='content',
            field=models.TextField(default='[To be filled in; you can use markup]'),
        ),
        migrations.AddField(
            model_name='journal',
            name='description',
            field=models.TextField(default='[To be filled in; you can use markup]'),
        ),
        migrations.AddField(
            model_name='journal',
            name='has_DOAJ_Seal',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='journal',
            name='scope',
            field=models.TextField(default='[To be filled in; you can use markup]'),
        ),
        migrations.AddField(
            model_name='journal',
            name='template_latex_tgz',
            field=models.FileField(blank=True, help_text='Gzipped tarball of the LaTeX template package', max_length=256, upload_to='UPLOADS/TEMPLATES/latex/%Y/', verbose_name='Template (LaTeX, gzipped tarball)'),
        ),
    ]
