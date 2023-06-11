# Generated by Django 4.0.1 on 2023-06-11 02:04

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("eznashdb", "0013_alter_room_is_wheelchair_accessible"),
    ]

    operations = [
        migrations.RenameField(
            model_name="room",
            old_name="is_same_floor_back",
            new_name="is_elevated_back",
        ),
        migrations.RenameField(
            model_name="room",
            old_name="is_same_floor_elevated",
            new_name="is_elevated_side",
        ),
        migrations.RenameField(
            model_name="room",
            old_name="is_same_floor_level",
            new_name="is_same_height_back",
        ),
        migrations.RenameField(
            model_name="room",
            old_name="is_same_floor_side",
            new_name="is_same_height_side",
        ),
    ]
