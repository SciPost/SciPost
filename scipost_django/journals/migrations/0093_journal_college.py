# Generated by Django 2.2.11 on 2020-09-06 07:03

from django.db import migrations


def populate_journal_college(apps, schema_editor):
    College = apps.get_model('colleges.College')
    Journal = apps.get_model('journals.Journal')

    for journal in Journal.objects.all():
        field_name = journal.name.split(' ')[1]
        if field_name != 'Selections':
            college = College.objects.get(name=field_name)
        else:
            college = College.objects.get(name='Multidisciplinary')
        journal.college = college
        journal.save()


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0092_auto_20200906_0903'),
    ]

    operations = [
        migrations.RunPython(populate_journal_college,
                             reverse_code=migrations.RunPython.noop),
    ]