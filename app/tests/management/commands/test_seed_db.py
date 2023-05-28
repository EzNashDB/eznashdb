from django.core.management import call_command

from app.management.commands.seed_db import Command as SeedDB
from eznashdb.models import Shul


def test_creates_a_user(django_user_model):
    call_command("seed_db")
    assert django_user_model.objects.count() == 1


def test_does_not_recreate_user(django_user_model):
    call_command("seed_db")
    call_command("seed_db")
    assert django_user_model.objects.count() == 1


def test_creates_shuls():
    call_command("seed_db")
    assert Shul.objects.count() == SeedDB.shul_count


def test_does_not_recreate_shuls():
    call_command("seed_db")
    call_command("seed_db")
    assert Shul.objects.count() == SeedDB.shul_count


def test_creates_at_least_1_room_per_shul():
    call_command("seed_db")
    for shul in Shul.objects.all():
        assert shul.rooms.count() >= 1


def test_does_not_recreate_rooms():
    for _ in range(4):
        call_command("seed_db")
    for shul in Shul.objects.all():
        assert shul.rooms.count() <= 3
