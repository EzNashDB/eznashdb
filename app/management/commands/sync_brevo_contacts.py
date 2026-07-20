from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from app import brevo

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Upsert all users with an email into the Brevo broadcast contact list. "
        "Safe to re-run anytime (e.g. before a campaign, to pick up new signups)."
    )

    def handle(self, *args, **options):
        if not brevo.is_enabled():
            self.stdout.write(
                self.style.WARNING("BREVO_API_KEY is not set. Skipping (nothing was synced).")
            )
            return

        users = User.objects.exclude(email="")
        synced_count = sum(1 for user in users if brevo.sync_contact(user) is not None)

        self.stdout.write(
            self.style.SUCCESS(f"Synced {synced_count} of {users.count()} user(s) to Brevo.")
        )
