# Generated by Django 5.1.1 on 2024-09-14 15:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0008_alter_simulatedinvestment_price_per_unit'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Holding',
        ),
    ]
