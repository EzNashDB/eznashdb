from datetime import date

from django.core.management import call_command
from freezegun import freeze_time

from app.models import GooglePlacesUsage


def test_deletes_records_older_than_3_months(db):
    GooglePlacesUsage.objects.create(date=date(2025, 10, 1))
    GooglePlacesUsage.objects.create(date=date(2026, 1, 1))

    with freeze_time("2026-03-01"):
        call_command("cleanup_google_places_usage_records")

    assert GooglePlacesUsage.objects.count() == 1
    assert GooglePlacesUsage.objects.first().date == date(2026, 1, 1)


def test_keeps_records_within_3_months(db):
    GooglePlacesUsage.objects.create(date=date(2025, 12, 1))
    GooglePlacesUsage.objects.create(date=date(2026, 2, 1))

    with freeze_time("2026-03-01"):
        call_command("cleanup_google_places_usage_records")

    assert GooglePlacesUsage.objects.count() == 2
