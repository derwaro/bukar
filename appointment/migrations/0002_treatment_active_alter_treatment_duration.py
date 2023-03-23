# Generated by Django 4.1.7 on 2023-03-14 16:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointment', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='treatment',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='treatment',
            name='duration',
            field=models.DurationField(default='00:15:00'),
        ),
    ]