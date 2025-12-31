import os
from typing import Any, Optional

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Set up Google OAuth credentials from environment variables"

    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")

        if not client_id or not client_secret:
            self.stdout.write(
                self.style.ERROR(
                    "Error: GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET "
                    "must be set in environment variables"
                )
            )
            return

        # Get or create the Google social app
        social_app, created = SocialApp.objects.update_or_create(
            provider="google",
            defaults={
                "name": "Google",
                "client_id": client_id,
                "secret": client_secret,
            },
        )

        # Add all sites to this social app
        sites = Site.objects.all()
        social_app.sites.set(sites)

        if created:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully created Google OAuth app for {sites.count()} site(s)")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully updated Google OAuth app for {sites.count()} site(s)")
            )
