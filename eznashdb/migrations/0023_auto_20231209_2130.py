# Generated by Django 4.0.1 on 2023-12-09 21:30

from django.db import migrations


def migrate(apps, schema_editor):
    Room = apps.get_model("eznashdb", "Room")
    old_size_to_new_size = {
        "XS": "S",
        "S": "M",
        "M": "L",
        "L": "L",
    }
    for room in Room.objects.all():
        if room.relative_size:
            room.relative_size = old_size_to_new_size[room.relative_size]
        room.save()


class Migration(migrations.Migration):
    dependencies = [
        ("eznashdb", "0022_shullink"),
    ]

    operations = [migrations.RunPython(migrate)]
