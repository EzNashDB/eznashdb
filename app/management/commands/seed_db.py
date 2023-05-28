from typing import Any, Optional

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from eznashdb.enums import RelativeSize, SeeHearScore
from eznashdb.models import Shul
from eznashdb.random import random_bool, random_bool_or_None, random_choice_or_blank

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database"
    user: User = None
    shul_count = 6
    rooms_per_shul = 2

    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        self.user, _ = User.objects.get_or_create(username="db_seeder")
        self.user.set_password("password")
        self._create_shuls()

    def _create_shuls(self):
        for i in range(self.shul_count):
            shul, _ = Shul.objects.update_or_create(
                name=f"Seeded Shul {i+1}",
                defaults={
                    "created_by": self.user,
                    "has_female_leadership": random_bool_or_None(),
                    "has_childcare": random_bool_or_None(),
                    "can_say_kaddish": random_bool_or_None(),
                },
            )
            self._create_shul_rooms(shul)

    def _create_shul_rooms(self, shul):
        shul_num = int(shul.name[-1])
        for j in range(self.rooms_per_shul):
            shul.rooms.update_or_create(
                name=f"Seeded Room {shul_num}-{j+1}",
                defaults={
                    "created_by": self.user,
                    "relative_size": random_choice_or_blank(list(RelativeSize)),
                    "see_hear_score": random_choice_or_blank(list(SeeHearScore)),
                    "is_same_floor_side": random_bool(),
                    "is_same_floor_back": random_bool(),
                    "is_same_floor_elevated": random_bool(),
                    "is_same_floor_level": random_bool(),
                    "is_balcony": random_bool(),
                    "is_only_men": random_bool(),
                    "is_mixed_seating": random_bool(),
                    "is_wheelchair_accessible": random_bool_or_None(),
                },
            )
