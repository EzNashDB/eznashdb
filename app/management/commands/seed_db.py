from django.core.management.base import BaseCommand
from typing import Any, Optional
from eznashdb.models import Shul
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database"
    user: User = None
    shul_count = 3
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
                    "has_female_leadership": bool(i % 2),
                    "has_childcare": bool((i + 1) % 2),
                    "can_say_kaddish": bool(i % 2),
                },
            )
            self._create_shul_rooms(shul)

    def _create_shul_rooms(self, shul):
        shul_num = shul.name[-1]
        for j in range(self.rooms_per_shul):
            shul.rooms.update_or_create(
                name=f"Seeded Room {shul_num}-{j+1}",
                defaults={
                    "created_by": self.user,
                },
            )
