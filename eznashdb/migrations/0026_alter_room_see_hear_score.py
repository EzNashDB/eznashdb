# Generated by Django 4.0.1 on 2023-12-10 15:06

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("eznashdb", "0025_alter_room_relative_size"),
    ]

    operations = [
        migrations.AlterField(
            model_name="room",
            name="see_hear_score",
            field=models.CharField(
                blank=True,
                choices=[
                    ("1", "1 (Much more difficult than men's section)"),
                    ("2", "2"),
                    ("3", "3"),
                    ("4", "4"),
                    ("5", "5 (Equal to men's section)"),
                ],
                default="",
                max_length=50,
            ),
        ),
    ]
