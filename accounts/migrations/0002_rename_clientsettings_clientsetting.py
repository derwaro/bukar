# Generated by Django 4.2.1 on 2023-05-25 16:12

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ClientSettings',
            new_name='ClientSetting',
        ),
    ]
