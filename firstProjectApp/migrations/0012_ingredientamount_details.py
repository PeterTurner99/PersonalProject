# Generated by Django 5.2a1 on 2025-02-19 13:51

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('firstProjectApp', '0011_alter_recipestep_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='ingredientamount',
            name='details',
            field=models.TextField(blank=True, null=True),
        ),
    ]
