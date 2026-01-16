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

        updated_shuls, deleted_shuls = self._get_shul_changes(days)

        if not updated_shuls and not deleted_shuls:
            self._log_no_changes()
            return

        template_context = self._prepare_template_context(updated_shuls, deleted_shuls)
        html_body = render_to_string("email/weekly_summary.html", template_context)

        if html_only:
            self.stdout.write(html_body)
            return

        self._send_email(html_body, len(updated_shuls), len(deleted_shuls))

    def _get_shul_changes(self, days):
        """Get recently updated and deleted shuls."""
        cutoff = timezone.now() - timedelta(days=days, hours=1)  # 1-hour buffer for edge cases

        updated_shuls = (
            Shul.objects.filter(Q(updated_at__gte=cutoff) | Q(rooms__updated_at__gte=cutoff))
            .distinct()
            .prefetch_related("rooms")
            .order_by("-updated_at")
        )

        deleted_shuls = (
            Shul.all_objects.filter(deleted__gte=cutoff)
            .select_related("deleted_by")
            .order_by("-deleted")
        )

        return updated_shuls, deleted_shuls

    def _prepare_template_context(self, updated_shuls, deleted_shuls):
        """Prepare context data for email template."""
        return {
            "shuls": [self._prepare_shul_data(shul) for shul in updated_shuls],
            "deleted_shuls": [self._prepare_deleted_shul_data(shul) for shul in deleted_shuls],
            "deleted_shuls_admin_url": self._build_deletedshul_admin_url(),
        }

    def _build_deletedshul_admin_url(self):
        """Build absolute URL to deleted shuls admin page."""
        admin_path = "/admin/eznashdb/deletedshul/"
        return f"{settings.SITE_URL}{admin_path}" if settings.SITE_URL else admin_path

    def _log_no_changes(self):
        """Log when no changes found."""
        self.stdout.write(
            self.style.SUCCESS("No shuls updated or deleted in the last week. Skipping email.")
        )

    def _send_email(self, html_body, updated_count, deleted_count):
        """Send summary email to superusers."""
        superusers = User.objects.filter(is_superuser=True, email__isnull=False)

        if not superusers:
            self.stdout.write(self.style.WARNING("No superusers with email addresses found. Skipping."))
            return

        subject = self._build_subject(updated_count, deleted_count)
        recipient_list = [user.email for user in superusers]

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
                f"{updated_count} shul(s) updated, {deleted_count} shul(s) deleted"
            )
        )

    def _build_subject(self, updated_count, deleted_count):
        """Build email subject with counts and date."""
        date_str = timezone.now().strftime("%B %d, %Y")
        return f"Weekly Shul Updates [{updated_count} updated, {deleted_count} deleted] - {date_str}"

    def _prepare_shul_data(self, shul):
        """Prepare shul data for template rendering."""
        return ShulData(
            name=shul.name,
            map_url=shul.get_map_url(absolute=True),
            country=self._get_country(shul.address),
            rooms=[self._prepare_room_data(room) for room in shul.rooms.all()],
            updated_at=shul.updated_at,
        )

    def _prepare_room_data(self, room):
        """Prepare room data for template rendering."""
        return RoomData(
            name=room.name,
            size=room.relative_size or "-",
            stars=self._format_stars(room.see_hear_score),
        )

    def _prepare_deleted_shul_data(self, shul):
        """Prepare deleted shul data for template rendering."""
        return DeletedShulData(
            name=shul.name,
            deletion_reason=shul.deletion_reason,
            deleted_by=shul.deleted_by.email if shul.deleted_by else "Unknown",
            deleted_at=shul.deleted,
            country=self._get_country(shul.address),
        )

    def _format_stars(self, score):
        """Convert numeric score to star rating."""
        if not score:
            return "-"

        score_int = int(score)
        return "★" * score_int + "☆" * (5 - score_int)

    def _get_country(self, address):
        """Extract country from address (last part after comma), or '-' for coordinates."""
        if not address or COORD_PATTERN.match(address.strip()):
            return "-"

        parts = address.split(",")
        return parts[-1].strip() if len(parts) > 1 else address.strip()
