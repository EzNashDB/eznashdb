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

        if not updated_shuls.exists():
            self.stdout.write(self.style.SUCCESS("No shuls updated in the last week. Skipping email."))
            return

        # Prepare data for template
        shuls_data = [self._prepare_shul_data(shul) for shul in updated_shuls]

        # Build HTML content
        html_body = render_to_string("email/weekly_summary.html", {"shuls": shuls_data})

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
        subject = f"Weekly Shul Updates [{shul_count}] - {timezone.now().strftime('%B %d, %Y')}"
        text_body = self._build_text_fallback(shuls_data)

        # Send email
        recipient_list = [u.email for u in superusers]
        send_mail(
            subject=subject,
            message=text_body,
            html_message=html_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Sent weekly summary to {len(recipient_list)} superuser(s): "
                f"{shul_count} shul(s) updated"
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

    def _build_text_fallback(self, shuls_data):
        """Build plain text fallback for email clients that don't support HTML."""
        lines = [f"Weekly Shul Updates - {len(shuls_data)} shul(s) updated", ""]

        for shul in shuls_data:
            lines.append(f"{shul.name}: {shul.map_url}")
            for room in shul.rooms:
                parts = [f"  - {room.name}"]
                if room.size != "-":
                    parts.append(room.size)
                if room.stars != "-":
                    parts.append(room.stars)
                lines.append(" | ".join(parts))
            lines.append("")

        return "\n".join(lines)
