# Generated by Django 2.1.8 on 2020-01-12 15:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('apimail', '0004_auto_20191114_2115'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('description', models.TextField()),
            ],
            options={
                'ordering': ['email'],
            },
        ),
        migrations.CreateModel(
            name='EmailAccountAccess',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rights', models.CharField(choices=[('CRUD', 'Can take all actions for this email account'), ('read', 'Can only view emails from/to this email account')], max_length=8)),
                ('date_from', models.DateField()),
                ('date_until', models.DateField()),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accesses', to='apimail.EmailAccount')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_account_accesses', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['account__email', 'user__last_name', '-date_until'],
            },
        ),
    ]
