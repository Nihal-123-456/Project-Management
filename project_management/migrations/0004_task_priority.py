# Generated by Django 5.1.2 on 2024-10-19 05:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project_management', '0003_task'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='priority',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
