from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.utils import timezone

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


def describe_send_weekly_summary():
    def describe_recipient_handling():
        def sends_to_superusers_only(superuser, regular_user, recent_shul):
            call_command("send_weekly_summary")

            assert len(mail.outbox) == 1
            assert mail.outbox[0].to == ["admin@example.com"]

        def handles_no_superusers(regular_user, recent_shul):
            call_command("send_weekly_summary")

            assert len(mail.outbox) == 0

        def skips_superusers_without_email(superuser_without_email, recent_shul):
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
        def includes_recently_updated_shuls(superuser, recent_shul):
            call_command("send_weekly_summary")

            assert len(mail.outbox) == 1
            html = mail.outbox[0].alternatives[0][0]
            assert "Recent Shul" in html

        def excludes_old_shuls(superuser, old_shul):
            call_command("send_weekly_summary")

            # No email sent when no recent updates
            assert len(mail.outbox) == 0

        def includes_shul_when_room_updated(superuser, old_shul):
            # Add a room that was updated recently
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
        def includes_shul_name_as_link(superuser, recent_shul):
            call_command("send_weekly_summary")

            html = mail.outbox[0].alternatives[0][0]  # HTML content
            assert '<a href="' in html
            assert "Recent Shul</a>" in html
            assert f"selectedShul={recent_shul.pk}" in html

        def includes_room_details(superuser, recent_shul):
            call_command("send_weekly_summary")

            html = mail.outbox[0].alternatives[0][0]
            assert "Main Sanctuary" in html
            assert ">M<" in html  # Size column just shows the letter
            assert "★★★★☆" in html  # 4/5 stars

        def extracts_country_from_address(superuser, recent_shul):
            # Address is "123 Main St" with city "Jerusalem"
            # Since there's no comma in address, it should show the whole address
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

        def has_subject_with_count(superuser, recent_shul):
            call_command("send_weekly_summary")

            subject = mail.outbox[0].subject
            assert "[1 updated, 0 deleted]" in subject
            assert "Weekly Shul Updates" in subject

        def includes_deleted_shul_count_in_subject(superuser, recent_shul, recently_deleted_shul):
            call_command("send_weekly_summary")

            subject = mail.outbox[0].subject
            assert "[1 updated, 1 deleted]" in subject

    def describe_deleted_shuls():
        def includes_recently_deleted_shuls(superuser, recently_deleted_shul):
            call_command("send_weekly_summary")

            assert len(mail.outbox) == 1
            html = mail.outbox[0].alternatives[0][0]
            assert "Recently Deleted Shul" in html

        def excludes_old_deleted_shuls(superuser, old_deleted_shul):
            call_command("send_weekly_summary")

            # No email sent when no recent updates or deletions
            assert len(mail.outbox) == 0

        def includes_deletion_reason(superuser, recently_deleted_shul):
            call_command("send_weekly_summary")

            html = mail.outbox[0].alternatives[0][0]
            assert "Test deletion" in html

        def includes_deleted_by_email(superuser, recently_deleted_shul):
            call_command("send_weekly_summary")

            html = mail.outbox[0].alternatives[0][0]
            assert "admin@example.com" in html

        def includes_deleted_shul_country(superuser, recently_deleted_shul):
            call_command("send_weekly_summary")

            html = mail.outbox[0].alternatives[0][0]
            assert "Israel" in html

        def sends_email_with_only_deleted_shuls(superuser, recently_deleted_shul):
            # No updated shuls, only deleted
            call_command("send_weekly_summary")

            assert len(mail.outbox) == 1
            subject = mail.outbox[0].subject
            assert "[0 updated, 1 deleted]" in subject

        def shows_no_reason_provided_when_missing(superuser, db):
            shul = Shul.objects.create(
                name="No Reason Shul",
                address="Test St",
                latitude=32.0,
                longitude=34.0,
            )
            shul.deleted_by = superuser
            shul.deletion_reason = ""
            shul.save()
            shul.delete()

            call_command("send_weekly_summary")

            html = mail.outbox[0].alternatives[0][0]
            assert "No Reason Shul" in html
            assert "(No reason provided)" in html

    def describe_custom_days():
        def respects_days_argument(superuser, old_shul):
            # With default 7 days, old_shul (10 days old) should not be included
            call_command("send_weekly_summary")
            assert len(mail.outbox) == 0

            # With 15 days, old_shul should be included
            call_command("send_weekly_summary", days=15)
            assert len(mail.outbox) == 1
            html = mail.outbox[0].alternatives[0][0]
            assert "Old Shul" in html

        def respects_days_argument_for_deleted_shuls(superuser, old_deleted_shul):
            # With default 7 days, old_deleted_shul (10 days old) should not be included
            call_command("send_weekly_summary")
            assert len(mail.outbox) == 0

            # With 15 days, old_deleted_shul should be included
            call_command("send_weekly_summary", days=15)
            assert len(mail.outbox) == 1
            html = mail.outbox[0].alternatives[0][0]
            assert "Old Deleted Shul" in html
