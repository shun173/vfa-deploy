# Generated by Django 2.2.5 on 2020-04-20 10:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecapp', '0001_initial'),
        ('users', '0003_auto_20200417_1619'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='fav_products',
            field=models.ManyToManyField(blank=True, to='ecapp.Product'),
        ),
    ]
