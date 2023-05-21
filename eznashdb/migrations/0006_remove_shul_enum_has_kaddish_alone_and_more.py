# Generated by Django 4.0.1 on 2023-04-30 07:36

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("eznashdb", "0005_remove_region_country_remove_shul_city_delete_city_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="shul",
            name="enum_has_kaddish_alone",
        ),
        migrations.RemoveField(
            model_name="shul",
            name="has_kaddish_with_men",
        ),
        migrations.AddField(
            model_name="shul",
            name="can_say_kaddish",
            field=models.BooleanField(blank=True, null=True),
        ),
    ]
