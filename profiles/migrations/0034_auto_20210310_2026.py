# Generated by Django 2.2.16 on 2021-03-10 19:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0033_auto_20200927_1658'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='title',
            field=models.CharField(blank=True, choices=[('PR', 'Prof.'), ('DR', 'Dr'), ('MR', 'Mr'), ('MRS', 'Mrs'), ('MS', 'Ms'), ('MX', 'Mx')], max_length=4, null=True),
        ),
    ]
