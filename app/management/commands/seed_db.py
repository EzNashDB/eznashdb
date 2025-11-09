import random
from typing import Any, Optional

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from faker import Faker

from eznashdb.enums import RelativeSize, SeeHearScore
from eznashdb.models import Room, Shul
from eznashdb.random import random_bool, random_bool_or_None, random_choice_or_blank

User = get_user_model()
fake = Faker()


class RoomCreator:
    def __init__(self, shul: Shul, room_number: int) -> None:
        self._shul = shul
        self._room_number = room_number

    def create(self):
        room, _ = self._shul.rooms.update_or_create(
            name=f"Dummy Room {self._room_number}",
            defaults={
                "created_by": self._shul.created_by,
                "relative_size": random_choice_or_blank(list(RelativeSize)),
                "see_hear_score": random_choice_or_blank(list(SeeHearScore)),
                "is_same_height_side": False,
                "is_same_height_back": False,
                "is_elevated_side": False,
                "is_elevated_back": False,
                "is_balcony": False,
                "is_only_men": False,
                "is_mixed_seating": False,
            },
        )
        return room


class HasWomenRoomCreator(RoomCreator):
    def create(self):
        room = super().create()
        params = {
            "is_same_height_side": random_bool(),
            "is_same_height_back": random_bool(),
            "is_elevated_side": random_bool(),
            "is_elevated_back": random_bool(),
            "is_balcony": random_bool(),
        }
        Room.objects.filter(pk=room.pk).update(**params)
        room.refresh_from_db()
        return room


class NoWomenRoomCreator(RoomCreator):
    def create(self):
        room = super().create()
        room.is_only_men = True
        return room.save()


class MixedSeatingRoomCreator(RoomCreator):
    def create(self):
        room = super().create()
        room.is_mixed_seating = True
        return room.save()


class Command(BaseCommand):
    help = "Seed the database"
    user: User = None
    shul_count = 6
    rooms_per_shul = 2
    room_creators = []

    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        self.user, _ = User.objects.get_or_create(username="db_seeder")
        self.user.set_password("password")
        self._create_shuls()

    def _create_shuls(self):
        for i in range(self.shul_count):
            shul, _ = Shul.objects.update_or_create(
                name=f"Dummy Shul {i + 1}",
                defaults={
                    "created_by": self.user,
                    "address": fake.street_address(),
                    "can_say_kaddish": random_bool_or_None(),
                },
            )
            self._create_shul_rooms(shul)

    def _create_shul_rooms(self, shul):
        room_count = random.choice([1, 2, 3])
        for j in range(room_count):
            self._get_random_room_creator()(shul, j + 1).create()

    def _get_random_room_creator(self) -> RoomCreator:
        choices = [NoWomenRoomCreator, MixedSeatingRoomCreator]
        for _ in range(3):
            choices.append(HasWomenRoomCreator)
        return random.choice(choices)
