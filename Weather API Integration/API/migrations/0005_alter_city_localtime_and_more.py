# Generated by Django 4.2.4 on 2023-10-31 15:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('API', '0004_alter_city_localtime_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='city',
            name='localtime',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='current_weather',
            name='last_updated',
            field=models.DateTimeField(null=True),
        ),
    ]
