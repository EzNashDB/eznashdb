from django.core.management.base import BaseCommand

from app.models import RateLimitViolation


class Command(BaseCommand):
    help = "Clear rate limit violations for an IP address"

    def add_arguments(self, parser):
        parser.add_argument("ip_address", type=str, help="IP address to clear")

    def handle(self, *args, **options):
        ip = options["ip_address"]
        count = RateLimitViolation.objects.filter(ip_address=ip).delete()[0]
        self.stdout.write(self.style.SUCCESS(f"Cleared {count} violations for {ip}"))
