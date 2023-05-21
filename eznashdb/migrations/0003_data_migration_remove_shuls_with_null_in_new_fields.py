# Generated by Django 4.0.1 on 2022-02-17 18:40

from django.db import migrations
from django.db.models import Q


def migrate(apps, schema_editor):
    Shul = apps.get_model("eznashdb", "Shul")
    bad_shuls = Shul.objects.filter(
        Q(created_by=None) | Q(updated_by=None) | Q(created_at=None) | Q(updated_at=None)
    )
    bad_shuls.delete()
    Room = apps.get_model("eznashdb", "Room")
    bad_rooms = Room.objects.filter(
        Q(created_by=None) | Q(updated_by=None) | Q(created_at=None) | Q(updated_at=None)
    )
    bad_rooms.delete()


def revert(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("eznashdb", "0002_rename_editted_by_shul_updated_by_room_created_at_and_more"),
    ]

    operations = [
        migrations.RunPython(migrate, revert),
    ]
