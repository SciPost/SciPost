# Generated by Django 3.2.16 on 2023-01-16 18:43

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('colleges', '0039_nomination_add_events'),
        ('submissions', '0132_auto_20221215_2034'),
    ]

    operations = [
        migrations.CreateModel(
            name='Qualification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('expert', 'Expert in this subject'), ('very_knowledgeable', 'Very knowledgeable in this subject'), ('knowledgeable', 'Knowledgeable in this subject'), ('marginally_qualified', 'Marginally qualified'), ('not_really_qualified', 'Not really qualified'), ('not_at_all_qualified', 'Not at all qualified')], max_length=32)),
                ('comments', models.TextField(blank=True)),
                ('datetime', models.DateTimeField(default=django.utils.timezone.now)),
                ('fellow', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='colleges.fellowship')),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='submissions.submission')),
            ],
            options={
                'ordering': ['submission', 'fellow'],
            },
        ),
        migrations.AddConstraint(
            model_name='qualification',
            constraint=models.UniqueConstraint(fields=('submission', 'fellow'), name='unique_together_submission_fellow'),
        ),
    ]