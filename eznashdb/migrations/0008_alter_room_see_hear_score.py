# Generated by Django 4.0.1 on 2023-05-07 17:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("eznashdb", "0007_alter_room_relative_size"),
    ]

    operations = [
        migrations.AlterField(
            model_name="room",
            name="see_hear_score",
            field=models.CharField(
                blank=True,
                choices=[
                    ("1", "Very difficult"),
                    ("2", "Difficult"),
                    ("3", "Moderate"),
                    ("4", "Easy"),
                    ("5", "Very easy"),
                ],
                max_length=50,
                null=True,
            ),
        ),
    ]
