# Generated by Django 4.0.1 on 2023-09-26 07:14

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("eznashdb", "0020_shul_city"),
    ]

    operations = [
        migrations.AddField(
            model_name="shul",
            name="latitude",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="shul",
            name="longitude",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="shul",
            name="place_id",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]