# Generated by Django 2.1.8 on 2019-10-16 14:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0084_journal_minimal_nr_of_reports'),
        ('scipost', '0033_auto_20191005_1142'),
        ('submissions', '0070_alternativerecommendation'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubmissionTiering',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tier', models.SmallIntegerField(choices=[(1, 'Tier I (surpasses expectations and criteria for this Journal; among top 10%)'), (2, 'Tier II (easily meets expectations and criteria for this Journal; among top 50%)'), (3, 'Tier III (meets expectations and criteria for this Journal)')])),
                ('fellow', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scipost.Contributor')),
                ('for_journal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='journals.Journal')),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tierings', to='submissions.Submission')),
            ],
        ),
    ]