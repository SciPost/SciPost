# Generated by Django 3.2.17 on 2023-02-15 16:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0023_subsidy_paid_on'),
    ]

    operations = [
        migrations.AddField(
            model_name='subsidyattachment',
            name='date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='subsidyattachment',
            name='kind',
            field=models.CharField(choices=[('agreement', 'Agreement'), ('invoice', 'Invoice'), ('proofofpayment', 'Proof of payment'), ('other', 'Other')], default='agreement', max_length=32),
        ),
    ]
