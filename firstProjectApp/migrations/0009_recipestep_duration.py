# Generated by Django 5.2a1 on 2025-02-17 12:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('firstProjectApp', '0008_remove_recipestep_duration_recipestep_shortdesc_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipestep',
            name='duration',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
