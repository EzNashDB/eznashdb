from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.utils import timezone

from app.enums import RateLimitedEndpoint
from app.models import RateLimitViolation
from eznashdb.models import Room, Shul

User = get_user_model()


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="password",
    )


@pytest.fixture
def superuser_without_email(db):
    return User.objects.create_superuser(
        username="admin_no_email",
        email="",
        password="password",
    )


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(
        username="regular",
        email="regular@example.com",
        password="password",
    )


@pytest.fixture
def recent_shul(db):
    shul = Shul.objects.create(
        name="Recent Shul",
        address="123 Main St",
        city="Jerusalem",
        latitude=31.7767,
        longitude=35.2345,
    )
    Room.objects.create(
        shul=shul,
        name="Main Sanctuary",
        relative_size="M",
        see_hear_score="4",
    )
    return shul


@pytest.fixture
def old_shul(db):
    shul = Shul.objects.create(
        name="Old Shul",
        address="456 Old St",
        latitude=31.7767,
        longitude=35.2345,
    )
    # Manually set updated_at to 10 days ago
    Shul.objects.filter(pk=shul.pk).update(updated_at=timezone.now() - timedelta(days=10))
    return Shul.objects.get(pk=shul.pk)


@pytest.fixture
def recently_deleted_shul(db, superuser):
    shul = Shul.objects.create(
        name="Recently Deleted Shul",
        address="789 Deleted St, Tel Aviv, Israel",
        city="Tel Aviv",
        latitude=32.0853,
        longitude=34.7818,
    )
    shul.deleted_by = superuser
    shul.deletion_reason = "Test deletion"
    shul.save()
    shul.delete()
    return Shul.all_objects.get(pk=shul.pk)


@pytest.fixture
def old_deleted_shul(db, superuser):
    shul = Shul.objects.create(
        name="Old Deleted Shul",
        address="999 Old Delete St",
        latitude=32.0853,
        longitude=34.7818,
    )
    shul.deleted_by = superuser
    shul.deletion_reason = "Old deletion"
    shul.save()
    shul.delete()
    # Manually set deleted timestamp to 10 days ago
    Shul.all_objects.filter(pk=shul.pk).update(deleted=timezone.now() - timedelta(days=10))
    return Shul.all_objects.get(pk=shul.pk)


@pytest.fixture
def recent_violation(db, regular_user):
    now = timezone.now()
    return RateLimitViolation.objects.create(
        ip_address="192.168.1.100",
        endpoint=RateLimitedEndpoint.COORDINATE_ACCESS,
        violation_count=3,
        first_violation_at=now - timedelta(days=2),
        last_violation_at=now - timedelta(minutes=30),  # Still in 1-hour cooldown
        user=regular_user,
    )


@pytest.fixture
def old_violation(db):
    old_time = timezone.now() - timedelta(days=10)
    return RateLimitViolation.objects.create(
        ip_address="192.168.1.200",
        endpoint=RateLimitedEndpoint.COORDINATE_ACCESS,
        violation_count=1,
        first_violation_at=old_time,
        last_violation_at=old_time,
        user=None,
    )


def describe_send_weekly_summary():
    def describe_recipient_handling():
        def sends_to_superusers_only(superuser, regular_user, recent_shul):
            call_command("send_weekly_summary")

            assert len(mail.outbox) == 1
            assert mail.outbox[0].to == ["admin@example.com"]

        def handles_no_superusers(regular_user, superuser_without_email, recent_shul):
            call_command("send_weekly_summary")
            assert len(mail.outbox) == 0

        def sends_to_multiple_superusers(superuser, recent_shul, db):
            User.objects.create_superuser(
                username="admin2",
                email="admin2@example.com",
                password="password",
            )

            call_command("send_weekly_summary")

            assert len(mail.outbox) == 1
            assert set(mail.outbox[0].to) == {"admin@example.com", "admin2@example.com"}

    def describe_shul_filtering():
        def includes_only_recent_updates(superuser, recent_shul, old_shul):
            # Recent shul should be included
            call_command("send_weekly_summary")
            assert len(mail.outbox) == 1
            html = mail.outbox[0].alternatives[0][0]
            assert "Recent Shul" in html

            # Verify old shul is excluded from same email
            assert "Old Shul" not in html

            # Verify count in subject shows only recent updates
            subject = mail.outbox[0].subject
            assert "[1 updated]" in subject

        def includes_shul_when_room_updated(superuser, old_shul):
            Room.objects.create(
                shul=old_shul,
                name="New Room",
                relative_size="L",
            )

            call_command("send_weekly_summary")

            assert len(mail.outbox) == 1
            html = mail.outbox[0].alternatives[0][0]
            assert "Old Shul" in html

    def describe_email_content():
        def includes_shul_details(superuser, recent_shul):
            call_command("send_weekly_summary")

            html = mail.outbox[0].alternatives[0][0]

            # Shul link and basic info
            assert '<a href="' in html
            assert "Recent Shul</a>" in html
            assert f"selectedShul={recent_shul.pk}" in html

            # Room details
            assert "Main Sanctuary" in html
            assert ">M<" in html  # Size column
            assert "★★★★☆" in html  # 4/5 stars

        def extracts_country_from_address(superuser, recent_shul):
            recent_shul.address = "123 Main St, Jerusalem, Israel"
            recent_shul.save()

            call_command("send_weekly_summary")

            html = mail.outbox[0].alternatives[0][0]
            assert ">Israel<" in html

        def shows_dash_for_coordinate_address(superuser, db):
            Shul.objects.create(
                name="Coord Shul",
                address="31.898692, 35.01042",
                latitude=31.898692,
                longitude=35.01042,
            )

            call_command("send_weekly_summary")

            html = mail.outbox[0].alternatives[0][0]
            assert "Coord Shul" in html
            # Country column should show "-"
            assert ">-<" in html

        def includes_deleted_shul_count_in_subject(superuser, recent_shul, recently_deleted_shul):
            call_command("send_weekly_summary")

            subject = mail.outbox[0].subject
            assert "[1 updated, 1 deleted]" in subject

    def describe_deleted_shuls():
        def includes_recently_deleted_shuls_with_details(
            superuser, recently_deleted_shul, old_deleted_shul
        ):
            call_command("send_weekly_summary")

            assert len(mail.outbox) == 1
            html = mail.outbox[0].alternatives[0][0]

            assert "Recently Deleted Shul" in html
            assert "Test deletion" in html
            assert "admin@example.com" in html  # Deleted by
            assert "Israel" in html  # Country

            assert "Old Deleted Shul" not in html

        def handles_email_with_only_deleted_shuls(superuser, recently_deleted_shul):
            # Test email with only deleted shuls, no updated ones
            mail.outbox.clear()
            call_command("send_weekly_summary")

            assert len(mail.outbox) == 1
            subject = mail.outbox[0].subject
            assert "[1 deleted]" in subject

    def describe_custom_days():
        def respects_days_argument_for_both_updated_and_deleted(superuser, old_shul, old_deleted_shul):
            # Default 7 days - should exclude both (10 days old)
            call_command("send_weekly_summary")
            assert len(mail.outbox) == 0

            # 15 days - should include both
            call_command("send_weekly_summary", days=15)
            assert len(mail.outbox) == 1
            html = mail.outbox[0].alternatives[0][0]
            assert "Old Shul" in html
            assert "Old Deleted Shul" in html

    def describe_rate_limit_violations():
        def includes_recent_violations_with_details(superuser, recent_violation, old_violation):
            call_command("send_weekly_summary")

            assert len(mail.outbox) == 1
            html = mail.outbox[0].alternatives[0][0]

            # Recent violation should be included
            assert "192.168.1.100" in html
            assert "Coordinate Access" in html
            assert ">3<" in html.replace("\n", "").replace(" ", "")
            assert "regular@example.com" in html
            # Should show blocked status (3rd violation = 1 hour cooldown)
            assert "Blocked until" in html

            # Old violation should not be included
            assert "192.168.1.200" not in html

        def shows_dash_for_no_user(superuser, db):
            RateLimitViolation.objects.create(
                ip_address="10.0.0.1",
                endpoint=RateLimitedEndpoint.COORDINATE_ACCESS,
                violation_count=1,
                first_violation_at=timezone.now(),
                last_violation_at=timezone.now(),
                user=None,
            )

            call_command("send_weekly_summary")

            assert len(mail.outbox) == 1
            html = mail.outbox[0].alternatives[0][0]
            assert "10.0.0.1" in html
            assert ">-<" in html  # No user, should show dash

        def includes_violation_count_in_subject(superuser, recent_violation):
            call_command("send_weekly_summary")

            subject = mail.outbox[0].subject
            assert "[1 violations]" in subject

        def respects_days_argument_for_violations(superuser, old_violation):
            # Default 7 days - should exclude (10 days old)
            call_command("send_weekly_summary")
            assert len(mail.outbox) == 0

            # 15 days - should include
            call_command("send_weekly_summary", days=15)
            assert len(mail.outbox) == 1
            html = mail.outbox[0].alternatives[0][0]
            assert "192.168.1.200" in html

        def includes_all_counts_when_mixed(
            superuser, recent_shul, recently_deleted_shul, recent_violation
        ):
            call_command("send_weekly_summary")

            subject = mail.outbox[0].subject
            assert "1 updated" in subject
            assert "1 deleted" in subject
            assert "1 violations" in subject

            html = mail.outbox[0].alternatives[0][0]
            assert "Recent Shul" in html
            assert "Recently Deleted Shul" in html
            assert "192.168.1.100" in html

        def shows_inactive_status_for_old_violations(superuser, db):
            # Create a violation from 2 days ago (outside the 24-hour active window)
            old_time = timezone.now() - timedelta(days=2)
            RateLimitViolation.objects.create(
                ip_address="10.0.0.99",
                endpoint=RateLimitedEndpoint.COORDINATE_ACCESS,
                violation_count=1,
                first_violation_at=old_time,
                last_violation_at=old_time,
                user=None,
            )

            call_command("send_weekly_summary")

            assert len(mail.outbox) == 1
            html = mail.outbox[0].alternatives[0][0]
            assert "10.0.0.99" in html
            assert "Inactive (&gt;24hrs old)" in html

        def shows_active_status_for_first_violation(superuser, db):
            # First violation has no cooldown, should show "Active"
            RateLimitViolation.objects.create(
                ip_address="10.0.0.88",
                endpoint=RateLimitedEndpoint.COORDINATE_ACCESS,
                violation_count=1,
                first_violation_at=timezone.now(),
                last_violation_at=timezone.now(),
                user=None,
            )

            call_command("send_weekly_summary")

            assert len(mail.outbox) == 1
            html = mail.outbox[0].alternatives[0][0]
            assert "10.0.0.88" in html
            assert "Active (&lt;24hrs, counts toward escalation)" in html
            assert "Blocked" not in html  # No cooldown for first violation

        def shows_cooldown_status_for_repeat_violations(superuser, db):
            # 4th violation should show 7-day cooldown
            now = timezone.now()
            RateLimitViolation.objects.create(
                ip_address="10.0.0.77",
                endpoint=RateLimitedEndpoint.COORDINATE_ACCESS,
                violation_count=4,
                first_violation_at=now - timedelta(days=1),
                last_violation_at=now,
                user=None,
            )

            call_command("send_weekly_summary")

            assert len(mail.outbox) == 1
            html = mail.outbox[0].alternatives[0][0]
            assert "10.0.0.77" in html
            assert "Blocked until" in html
