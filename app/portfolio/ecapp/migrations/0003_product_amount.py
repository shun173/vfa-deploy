# Generated by Django 2.2.5 on 2020-04-28 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecapp', '0002_product_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='amount',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
