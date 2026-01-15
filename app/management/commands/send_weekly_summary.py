import re
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone

from eznashdb.models import Shul

User = get_user_model()

# Pattern to detect coordinate-only addresses (e.g., "31.898692, 35.01042")
COORD_PATTERN = re.compile(r"^-?\d+\.?\d*\s*,\s*-?\d+\.?\d*$")


@dataclass
class RoomData:
    name: str
    size: str
    stars: str


@dataclass
class ShulData:
    name: str
    map_url: str
    country: str
    rooms: list[RoomData]
    updated_at: object  # datetime object for template formatting


@dataclass
class DeletedShulData:
    name: str
    deletion_reason: str
    deleted_by: str
    deleted_at: object  # datetime object for template formatting
    country: str


class Command(BaseCommand):
    help = "Send weekly summary email of shul changes to superusers"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Number of days to look back (default: 7)",
        )
        parser.add_argument(
            "--html",
            action="store_true",
            help="Output HTML to stdout instead of sending email",
        )

    def handle(self, *args, **options):
        days = options["days"]
        html_only = options["html"]

        # Calculate cutoff with 1-hour buffer for edge cases
        cutoff = timezone.now() - timedelta(days=days, hours=1)

        # Get updated shuls (check both shul and room updated_at)
        updated_shuls = (
            Shul.objects.filter(Q(updated_at__gte=cutoff) | Q(rooms__updated_at__gte=cutoff))
            .distinct()
            .prefetch_related("rooms")
            .order_by("-updated_at")
        )

        # Get deleted shuls (using all_objects to include soft-deleted)
        deleted_shuls = (
            Shul.all_objects.filter(deleted__gte=cutoff)
            .select_related("deleted_by")
            .order_by("-deleted")
        )

        if not updated_shuls.exists() and not deleted_shuls.exists():
            self.stdout.write(
                self.style.SUCCESS("No shuls updated or deleted in the last week. Skipping email.")
            )
            return

        # Prepare data for template
        shuls_data = [self._prepare_shul_data(shul) for shul in updated_shuls]
        deleted_shuls_data = [self._prepare_deleted_shul_data(shul) for shul in deleted_shuls]

        # Build absolute URL to deleted shuls admin page
        deleted_shuls_admin_path = "/admin/eznashdb/deletedshul/"
        deleted_shuls_admin_url = (
            f"{settings.SITE_URL}{deleted_shuls_admin_path}"
            if settings.SITE_URL
            else deleted_shuls_admin_path
        )

        # Build HTML content
        html_body = render_to_string(
            "email/weekly_summary.html",
            {
                "shuls": shuls_data,
                "deleted_shuls": deleted_shuls_data,
                "deleted_shuls_admin_url": deleted_shuls_admin_url,
            },
        )

        # If --html flag, just output HTML and exit
        if html_only:
            self.stdout.write(html_body)
            return

        # Get superusers with email addresses
        superusers = User.objects.filter(is_superuser=True, email__isnull=False)

        if not superusers:
            self.stdout.write(self.style.WARNING("No superusers with email addresses found. Skipping."))
            return

        # Build email content
        shul_count = len(shuls_data)
        deleted_count = len(deleted_shuls_data)
        subject = f"Weekly Shul Updates [{shul_count} updated, {deleted_count} deleted] - {timezone.now().strftime('%B %d, %Y')}"

        # Send email
        recipient_list = [u.email for u in superusers]
        send_mail(
            subject=subject,
            message="",  # Gmail supports HTML, no need for text fallback
            html_message=html_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Sent weekly summary to {len(recipient_list)} superuser(s): "
                f"{shul_count} shul(s) updated, {deleted_count} shul(s) deleted"
            )
        )

    def _prepare_shul_data(self, shul):
        """Prepare shul data for template rendering."""
        rooms_data = []
        for room in shul.rooms.all():
            stars = "-"
            if room.see_hear_score:
                score = int(room.see_hear_score)
                stars = "★" * score + "☆" * (5 - score)

            rooms_data.append(
                RoomData(
                    name=room.name,
                    size=room.relative_size or "-",
                    stars=stars,
                )
            )

        return ShulData(
            name=shul.name,
            map_url=shul.get_map_url(absolute=True),
            country=self._get_country(shul.address),
            rooms=rooms_data,
            updated_at=shul.updated_at,
        )

    def _prepare_deleted_shul_data(self, shul):
        """Prepare deleted shul data for template rendering."""
        deleted_by_email = shul.deleted_by.email if shul.deleted_by else "Unknown"

        return DeletedShulData(
            name=shul.name,
            deletion_reason=shul.deletion_reason,
            deleted_by=deleted_by_email,
            deleted_at=shul.deleted,
            country=self._get_country(shul.address),
        )

    def _get_country(self, address):
        """Extract country from address (last part after comma), or '-' for coordinates."""
        if not address:
            return "-"
        if COORD_PATTERN.match(address.strip()):
            return "-"
        parts = address.split(",")
        if len(parts) > 1:
            return parts[-1].strip()
        return address.strip()
