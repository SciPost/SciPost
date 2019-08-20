# Generated by Django 2.1.8 on 2019-08-20 10:20

from django.db import migrations, models


def populate_journal_names(apps, schema_editor):
    Journal = apps.get_model('journals.Journal')

    for journal in Journal.objects.all():
        if journal.name == 'SciPostPhys':
            journal.name = 'SciPost Physics'
            journal.name_abbrev = 'SciPost Phys.'
        elif journal.name == 'SciPostPhysLectNotes':
            journal.name = 'SciPost Physics Lecture Notes'
            journal.name_abbrev = 'SciPost Phys. Lect. Notes'
        elif journal.name == 'SciPostPhysProc':
            journal.name = 'SciPost Physics Proceedings'
            journal.name_abbrev = 'SciPost Phys. Proc.'
        elif journal.name == 'SciPostPhysCodeb':
            journal.name = 'SciPost Physics Codebases'
            journal.name_abbrev = 'SciPost Phys. Codeb.'
        elif journal.name == 'SciPostPhysComm':
            journal.name = 'SciPost Physics Commons'
            journal.name_abbrev = 'SciPost Phys. Comm.'
        journal.save()


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0066_auto_20190819_1149'),
    ]

    operations = [
        migrations.AddField(
            model_name='journal',
            name='name_abbrev',
            field=models.CharField(default='SciPost [abbrev]', help_text='Abbreviated name (for use in citations)', max_length=128),
        ),
        migrations.RunPython(populate_journal_names,
                             reverse_code=migrations.RunPython.noop),
    ]
