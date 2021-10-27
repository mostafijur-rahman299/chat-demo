# Generated by Django 3.1.4 on 2020-12-09 13:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_auto_20201209_1901'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(blank=True, max_length=25, null=True),
        ),
    ]
