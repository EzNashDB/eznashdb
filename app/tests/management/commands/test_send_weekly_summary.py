from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from freezegun import freeze_time

from app.abuse_config import PERMANENT_BAN_THRESHOLD
from app.models import AbuseState, GooglePlacesUsage, GooglePlacesUserUsage
from eznashdb.models import Room, Shul

User = get_user_model()


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
def recent_abuse_state(db, regular_user):
    now = timezone.now()
    return AbuseState.objects.create(
        user=regular_user,
        points=3,
        episode_started_at=now - timedelta(days=2),
        last_violation_at=now - timedelta(minutes=30),
        cooldown_until=now + timedelta(hours=1),
    )


@pytest.fixture
def old_abuse_state(db):
    user = User.objects.create_user(username="olduser", email="old@example.com", password="pass")
    old_time = timezone.now() - timedelta(days=10)
    return AbuseState.objects.create(
        user=user,
        points=1,
        last_violation_at=old_time,
    )


def describe_send_weekly_summary():
    def describe_recipient_handling():
        def sends_to_superusers_only(superuser, regular_user, recent_shul, mailoutbox):
            call_command("send_weekly_summary")

            assert len(mailoutbox) == 1
            assert mailoutbox[0].to == ["admin@example.com"]

        def handles_no_superusers(regular_user, superuser_without_email, recent_shul, mailoutbox):
            call_command("send_weekly_summary")
            assert len(mailoutbox) == 0

        def sends_to_multiple_superusers(superuser, recent_shul, db, mailoutbox):
            User.objects.create_superuser(
                username="admin2",
                email="admin2@example.com",
                password="password",
            )

            call_command("send_weekly_summary")

            assert len(mailoutbox) == 1
            assert set(mailoutbox[0].to) == {"admin@example.com", "admin2@example.com"}

    def describe_shul_filtering():
        def includes_only_recent_updates(superuser, recent_shul, old_shul, mailoutbox):
            call_command("send_weekly_summary")
            assert len(mailoutbox) == 1
            html = mailoutbox[0].alternatives[0][0]
            assert "Recent Shul" in html
            assert "Old Shul" not in html

            subject = mailoutbox[0].subject
            assert "[1 updated]" in subject

        def includes_shul_when_room_updated(superuser, old_shul, mailoutbox):
            Room.objects.create(
                shul=old_shul,
                name="New Room",
                relative_size="L",
            )

            call_command("send_weekly_summary")

            assert len(mailoutbox) == 1
            html = mailoutbox[0].alternatives[0][0]
            assert "Old Shul" in html

    def describe_email_content():
        def includes_shul_details(superuser, recent_shul, mailoutbox):
            call_command("send_weekly_summary")

            html = mailoutbox[0].alternatives[0][0]
            assert '<a href="' in html
            assert "Recent Shul</a>" in html
            assert f"selectedShul={recent_shul.pk}" in html
            assert "Main Sanctuary" in html
            assert ">M<" in html
            assert "★★★★☆" in html

        def extracts_country_from_address(superuser, recent_shul, mailoutbox):
            recent_shul.address = "123 Main St, Jerusalem, Israel"
            recent_shul.save()

            call_command("send_weekly_summary")

            html = mailoutbox[0].alternatives[0][0]
            assert ">Israel<" in html

        def shows_dash_for_coordinate_address(superuser, db, mailoutbox):
            Shul.objects.create(
                name="Coord Shul",
                address="31.898692, 35.01042",
                latitude=31.898692,
                longitude=35.01042,
            )

            call_command("send_weekly_summary")

            html = mailoutbox[0].alternatives[0][0]
            assert "Coord Shul" in html
            assert ">-<" in html

        def includes_deleted_shul_count_in_subject(
            superuser, recent_shul, recently_deleted_shul, mailoutbox
        ):
            call_command("send_weekly_summary")

            subject = mailoutbox[0].subject
            assert "[1 updated, 1 deleted]" in subject

    def describe_deleted_shuls():
        def includes_recently_deleted_shuls_with_details(
            superuser, recently_deleted_shul, old_deleted_shul, mailoutbox
        ):
            call_command("send_weekly_summary")

            assert len(mailoutbox) == 1
            html = mailoutbox[0].alternatives[0][0]

            assert "Recently Deleted Shul" in html
            assert "Test deletion" in html
            assert "admin@example.com" in html  # Deleted by
            assert "Israel" in html  # Country

            assert "Old Deleted Shul" not in html

        def handles_email_with_only_deleted_shuls(superuser, recently_deleted_shul, mailoutbox):
            mailoutbox.clear()
            call_command("send_weekly_summary")

            assert len(mailoutbox) == 1
            subject = mailoutbox[0].subject
            assert "[1 deleted]" in subject

    def describe_custom_days():
        def respects_days_argument_for_both_updated_and_deleted(
            superuser, old_shul, old_deleted_shul, mailoutbox
        ):
            call_command("send_weekly_summary")
            assert len(mailoutbox) == 0

            call_command("send_weekly_summary", days=15)
            assert len(mailoutbox) == 1
            html = mailoutbox[0].alternatives[0][0]
            assert "Old Shul" in html
            assert "Old Deleted Shul" in html

    def describe_abuse_states():
        def includes_recent_abuse_states_with_details(
            superuser, recent_abuse_state, old_abuse_state, mailoutbox
        ):
            call_command("send_weekly_summary")

            assert len(mailoutbox) == 1
            html = mailoutbox[0].alternatives[0][0]
            assert "regular@example.com" in html
            assert ">3<" in html.replace("\n", "").replace(" ", "")
            assert "Blocked until" in html
            assert "old@example.com" not in html

        def includes_abuse_count_in_subject(superuser, recent_abuse_state, mailoutbox):
            call_command("send_weekly_summary")

            subject = mailoutbox[0].subject
            assert "[1 abuse]" in subject

        def respects_days_argument_for_abuse_states(superuser, old_abuse_state, mailoutbox):
            call_command("send_weekly_summary")
            assert len(mailoutbox) == 0

            call_command("send_weekly_summary", days=15)
            assert len(mailoutbox) == 1
            html = mailoutbox[0].alternatives[0][0]
            assert "old@example.com" in html

        def includes_all_counts_when_mixed(
            superuser, recent_shul, recently_deleted_shul, recent_abuse_state, mailoutbox
        ):
            call_command("send_weekly_summary")

            subject = mailoutbox[0].subject
            assert "1 updated" in subject
            assert "1 deleted" in subject
            assert "1 abuse" in subject

            html = mailoutbox[0].alternatives[0][0]
            assert "Recent Shul" in html
            assert "Recently Deleted Shul" in html
            assert "regular@example.com" in html

        def shows_permanently_banned_status(superuser, db, mailoutbox):
            user = User.objects.create_user(
                username="banned", email="banned@example.com", password="pass"
            )
            AbuseState.objects.create(
                user=user,
                points=PERMANENT_BAN_THRESHOLD,
                last_violation_at=timezone.now(),
            )

            call_command("send_weekly_summary")

            assert len(mailoutbox) == 1
            html = mailoutbox[0].alternatives[0][0]
            assert "banned@example.com" in html
            assert "PERMANENTLY BANNED" in html

        def shows_captcha_required_status_for_active_users(superuser, db, mailoutbox):
            user = User.objects.create_user(
                username="active", email="active@example.com", password="pass"
            )
            AbuseState.objects.create(
                user=user,
                points=1,
                last_violation_at=timezone.now(),
            )

            call_command("send_weekly_summary")

            assert len(mailoutbox) == 1
            html = mailoutbox[0].alternatives[0][0]
            assert "active@example.com" in html
            assert "Active (CAPTCHA required)" in html

    def describe_google_places_usage():
        def shows_usage_section_with_weekly_and_monthly_totals(superuser, db, mailoutbox):
            now = timezone.now()

            GooglePlacesUsage.objects.create(
                date=(now - timedelta(days=2)).date(),
                autocomplete_requests=100,
                details_requests=50,
            )
            GooglePlacesUsage.objects.create(
                date=(now - timedelta(days=5)).date(),
                autocomplete_requests=200,
                details_requests=75,
            )
            GooglePlacesUsage.objects.create(
                date=(now - timedelta(days=1)).date(),
                autocomplete_requests=50,
                details_requests=25,
            )

            call_command("send_weekly_summary")

            assert len(mailoutbox) == 1
            html = mailoutbox[0].alternatives[0][0]
            assert ">350<" in html
            assert ">150<" in html
            assert "350/10000 (3%)" in html
            assert "150/10000 (1%)" in html

        def aggregates_weekly_totals_across_multiple_days(superuser, db, mailoutbox):
            now = timezone.now()

            for i in range(1, 8):
                GooglePlacesUsage.objects.create(
                    date=(now - timedelta(days=i)).date(),
                    autocomplete_requests=10,
                    details_requests=5,
                )

            call_command("send_weekly_summary")

            assert len(mailoutbox) == 1
            html = mailoutbox[0].alternatives[0][0]
            assert ">70<" in html
            assert ">35<" in html

        def calculates_monthly_percentages(superuser, db, mailoutbox):
            now = timezone.now()

            GooglePlacesUsage.objects.create(
                date=(now - timedelta(days=1)).date(),
                autocomplete_requests=5000,
                details_requests=2000,
            )

            call_command("send_weekly_summary")

            assert len(mailoutbox) == 1
            html = mailoutbox[0].alternatives[0][0]
            assert "(50%)" in html
            assert "(20%)" in html

        def respects_days_argument(superuser, db, mailoutbox):
            now = timezone.now()

            GooglePlacesUsage.objects.create(
                date=(now - timedelta(days=10)).date(),
                autocomplete_requests=100,
                details_requests=50,
            )

            call_command("send_weekly_summary")
            assert len(mailoutbox) == 0

            call_command("send_weekly_summary", days=15)
            assert len(mailoutbox) == 1
            html = mailoutbox[0].alternatives[0][0]
            assert ">100<" in html
            assert ">50<" in html

        def shows_user_limit_hits_when_present(superuser, regular_user, db, mailoutbox):
            now = timezone.now()

            GooglePlacesUsage.objects.create(
                date=(now - timedelta(days=1)).date(),
                autocomplete_requests=100,
                details_requests=50,
            )

            user2 = User.objects.create_user(username="user2", email="user2@example.com")
            GooglePlacesUserUsage.objects.create(
                user=regular_user,
                date=(now - timedelta(days=2)).date(),
                autocomplete_requests=settings.GOOGLE_PLACES_USER_DAILY_AUTOCOMPLETE_LIMIT,
            )
            GooglePlacesUserUsage.objects.create(
                user=regular_user,
                date=(now - timedelta(days=4)).date(),
                autocomplete_requests=settings.GOOGLE_PLACES_USER_DAILY_AUTOCOMPLETE_LIMIT,
            )
            GooglePlacesUserUsage.objects.create(
                user=user2,
                date=(now - timedelta(days=3)).date(),
                autocomplete_requests=settings.GOOGLE_PLACES_USER_DAILY_AUTOCOMPLETE_LIMIT,
            )
            GooglePlacesUserUsage.objects.create(
                user=user2,
                date=(now - timedelta(days=1)).date(),
                autocomplete_requests=settings.GOOGLE_PLACES_USER_DAILY_AUTOCOMPLETE_LIMIT - 20,
            )

            call_command("send_weekly_summary")

            assert len(mailoutbox) == 1
            html = mailoutbox[0].alternatives[0][0]
            assert ">User limit hits<" in html
            assert ">3<" in html

        @freeze_time("2026-02-10 02:00:00")  # >7 days into the month
        def shows_monthly_user_limit_hits(superuser, regular_user, db, mailoutbox):
            now = timezone.now()
            first_day_of_month = now.date().replace(day=1)

            GooglePlacesUsage.objects.create(
                date=(now - timedelta(days=1)).date(),
                autocomplete_requests=100,
                details_requests=50,
            )

            user2 = User.objects.create_user(username="user2", email="user2@example.com")
            GooglePlacesUserUsage.objects.create(
                user=regular_user,
                date=(now - timedelta(days=2)).date(),
                autocomplete_requests=settings.GOOGLE_PLACES_USER_DAILY_AUTOCOMPLETE_LIMIT,
            )
            GooglePlacesUserUsage.objects.create(
                user=user2,
                date=(now - timedelta(days=4)).date(),
                autocomplete_requests=settings.GOOGLE_PLACES_USER_DAILY_AUTOCOMPLETE_LIMIT,
            )

            user3 = User.objects.create_user(username="user3", email="user3@example.com")
            GooglePlacesUserUsage.objects.create(
                user=user3,
                date=first_day_of_month,
                autocomplete_requests=settings.GOOGLE_PLACES_USER_DAILY_AUTOCOMPLETE_LIMIT,
            )

            call_command("send_weekly_summary")

            assert len(mailoutbox) == 1
            html = mailoutbox[0].alternatives[0][0]
            stripped_html = html.replace("\n", "").replace(" ", "")
            assert ">User limit hits<" in html
            assert ">2<" in stripped_html
            assert ">3<" in stripped_html
