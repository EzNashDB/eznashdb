from django.core.management import call_command

from eznashdb.models import Shul


def test_creates_a_user(django_user_model):
    call_command("seed_db")
    assert django_user_model.objects.count() == 1


def test_does_not_recreate_user(django_user_model):
    call_command("seed_db")
    call_command("seed_db")
    assert django_user_model.objects.count() == 1


def test_creates_3_shuls():
    call_command("seed_db")
    assert Shul.objects.count() == 3


def test_does_not_recreate_shuls():
    call_command("seed_db")
    call_command("seed_db")
    assert Shul.objects.count() == 3


def test_creates_2_rooms_per_shul():
    call_command("seed_db")
    for shul in Shul.objects.all():
        assert shul.rooms.count() == 2


def test_does_not_recreate_rooms():
    call_command("seed_db")
    call_command("seed_db")
    for shul in Shul.objects.all():
        assert shul.rooms.count() == 2
