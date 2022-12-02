from django.core.management.base import BaseCommand
from typing import Any, Optional
from eznashdb.models import Shul
from django.contrib.auth import get_user_model
from eznashdb.enums import KaddishAlone
User = get_user_model()

class Command(BaseCommand):
    help = 'Seed the database'

    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        user, _ = User.objects.get_or_create(username="db_seeder")
        user.set_password("password")
        for i in range(3):
            Shul.objects.update_or_create(
                name=f"Seeded Shul {i+1}",
                defaults={
                    "created_by":user,
                    "has_female_leadership": bool(i%2),
                    "has_childcare": bool((i+1)%2),
                    "has_kaddish_with_men": bool(i%2),
                    "enum_has_kaddish_alone": list(KaddishAlone)[i]
                }
            )