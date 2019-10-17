# Generated by Django 2.1.8 on 2019-10-05 09:22

from django.db import migrations, models


def from_astrophysics_to_astronomy(apps, schema_editor):
    Contributor = apps.get_model('scipost', 'Contributor')

    Contributor.objects.filter(discipline='astrophysics').update(discipline='astronomy')


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0031_auto_20190926_0603'),
    ]

    operations = [
        migrations.RunPython(from_astrophysics_to_astronomy,
                            reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='contributor',
            name='discipline',
            field=models.CharField(choices=[('Multidisciplinary', (('multidisciplinary', 'Multidisciplinary'),)), ('Formal Sciences', (('mathematics', 'Mathematics'), ('computerscience', 'Computer Science'))), ('Natural Sciences', (('physics', 'Physics'), ('astronomy', 'Astronomy'), ('biology', 'Biology'), ('chemistry', 'Chemistry'), ('earthscience', 'Earth and Environmental Sciences'))), ('Engineering', (('civileng', 'Civil Engineering'), ('electricaleng', 'Electrical Engineering'), ('mechanicaleng', 'Mechanical Engineering'), ('chemicaleng', 'Chemical Engineering'), ('materialseng', 'Materials Engineering'), ('medicaleng', 'Medical Engineering'), ('environmentaleng', 'Environmental Engineering'), ('industrialeng', 'Industrial Engineering'))), ('Medical Sciences', (('medicine', 'Basic Medicine'), ('clinical', 'Clinical Medicine'), ('health', 'Health Sciences'))), ('Agricultural Sciences', (('agricultural', 'Agriculture, Forestry and Fisheries'), ('veterinary', 'Veterinary Science'))), ('Social Sciences', (('economics', 'Economics'), ('geography', 'Geography'), ('law', 'Law'), ('media', 'Media and Communications'), ('pedagogy', 'Pedagogy and Educational Sciences'), ('politicalscience', 'Political Science'), ('psychology', 'Psychology'), ('sociology', 'Sociology'))), ('Humanities', (('art', 'Art (arts, history or arts, performing arts, music)'), ('history', 'History and Archeology'), ('literature', 'Language and Literature'), ('philosophy', 'Philosophy, Ethics and Religion')))], default='physics', max_length=20, verbose_name='Main discipline'),
        ),
    ]