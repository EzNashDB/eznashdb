"""Management command to cleanup old Google Places usage records."""

from datetime import date

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand

from app.models import GooglePlacesUsage, GooglePlacesUserUsage


class Command(BaseCommand):
    """Delete old Google Places usage records (keeps 3 months)."""

    help = "Delete old Google Places usage records (keeps 3 months)"

    def handle(self, *args, **options):
        """Execute the cleanup."""
        # Keep 3 months of history
        cutoff = date.today().replace(day=1) - relativedelta(months=3)

        global_deleted, _ = GooglePlacesUsage.objects.filter(date__lt=cutoff).delete()
        user_deleted, _ = GooglePlacesUserUsage.objects.filter(date__lt=cutoff).delete()

        self.stdout.write(
            self.style.SUCCESS(f"Deleted {global_deleted} global and {user_deleted} user usage records")
        )
