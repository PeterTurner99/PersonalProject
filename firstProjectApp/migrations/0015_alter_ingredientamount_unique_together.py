# Generated by Django 5.2a1 on 2025-02-27 16:13

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('firstProjectApp', '0014_alter_ingredient_unique_together'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='ingredientamount',
            unique_together={('ingredient', 'amount', 'units')},
        ),
    ]
