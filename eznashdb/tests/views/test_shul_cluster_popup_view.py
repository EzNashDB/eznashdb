from datetime import timedelta

import pytest
from bs4 import BeautifulSoup
from constance import config
from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from app.models import AbuseState
from eznashdb.enums import RelativeSize, SeeHearScore
from eznashdb.models import Shul
from eznashdb.views import ShulClusterPopupView


@pytest.fixture
def popup_GET(rf_GET, test_user):
    def _get(user=test_user, **query_params):
        request = rf_GET("eznashdb:cluster_popup", query_params=query_params, htmx=True)
        request.user = user
        return request

    return _get


def test_returns_only_shuls_in_the_requested_cluster(popup_GET):
    # Same rounded coords -> same cluster
    here = Shul.objects.create(name="Here", latitude=40.7128, longitude=-74.0060)
    also = Shul.objects.create(name="Also Here", latitude=40.7129, longitude=-74.0061)
    far = Shul.objects.create(name="Far Away", latitude=31.7683, longitude=35.2137)
    assert here.cluster_key == also.cluster_key
    assert here.cluster_key != far.cluster_key

    response = ShulClusterPopupView.as_view()(popup_GET(cluster_key=here.cluster_key))
    content = response.content.decode()

    assert here.name in content
    assert also.name in content
    assert far.name not in content


def test_missing_cluster_key_is_a_bad_request(popup_GET):
    response = ShulClusterPopupView.as_view()(popup_GET())

    assert response.status_code == 400


def test_unknown_cluster_key_renders_an_empty_state(popup_GET, test_shul):
    response = ShulClusterPopupView.as_view()(popup_GET(cluster_key="0.0_0.0"))

    assert test_shul.name not in response.content.decode()
    assert "no longer available" in response.content.decode().lower()


def test_soft_deleted_shuls_are_not_returned(popup_GET, test_shul):
    cluster_key = test_shul.cluster_key
    test_shul.delete()

    content = ShulClusterPopupView.as_view()(popup_GET(cluster_key=cluster_key)).content.decode()

    assert test_shul.name not in content


def test_shul_name_is_html_escaped(popup_GET, test_shul):
    test_shul.name = "'`</script><img src=x onerror=alert(1)>"
    test_shul.save()

    content = ShulClusterPopupView.as_view()(
        popup_GET(cluster_key=test_shul.cluster_key)
    ).content.decode()

    assert "<img src=x onerror" not in content
    assert "</script><img" not in content


def describe_rooms():
    @pytest.mark.parametrize(("relative_size"), list(RelativeSize))
    def test_shows_room_relative_size(test_shul, popup_GET, relative_size):
        test_shul.rooms.create(name="test_room", relative_size=relative_size)

        content = ShulClusterPopupView.as_view()(
            popup_GET(cluster_key=test_shul.cluster_key)
        ).content.decode()

        assert str(relative_size.label) in content

    def test_displays_dash_for_unknown_relative_size(test_shul, popup_GET):
        test_shul.rooms.create(name="test_room", relative_size="", see_hear_score=SeeHearScore._3)

        content = ShulClusterPopupView.as_view()(
            popup_GET(cluster_key=test_shul.cluster_key)
        ).content.decode()

        assert "--" in content

    @pytest.mark.parametrize(("see_hear_score"), list(SeeHearScore))
    def test_shows_room_see_hear_score(test_shul, popup_GET, see_hear_score):
        test_shul.rooms.create(name="test_room", see_hear_score=see_hear_score)

        content = ShulClusterPopupView.as_view()(
            popup_GET(cluster_key=test_shul.cluster_key)
        ).content.decode()

        expected_filled_star_count = int(see_hear_score.value)
        expected_empty_star_count = 5 - expected_filled_star_count

        assert content.count("fa-solid fa-star") == expected_filled_star_count
        assert content.count("fa-regular fa-star") == expected_empty_star_count

    def test_shows_dash_for_unknown_see_hear_score(test_shul, popup_GET):
        test_shul.rooms.create(name="test_room", see_hear_score="", relative_size=RelativeSize.M)

        content = ShulClusterPopupView.as_view()(
            popup_GET(cluster_key=test_shul.cluster_key)
        ).content.decode()

        assert "--" in content


def describe_filters():
    def test_applies_the_forwarded_filters(popup_GET):
        large = Shul.objects.create(name="Large Room", latitude=40.7128, longitude=-74.0060)
        small = Shul.objects.create(name="Small Room", latitude=40.7129, longitude=-74.0061)
        large.rooms.create(name="r", relative_size=RelativeSize.L)
        small.rooms.create(name="r", relative_size=RelativeSize.S)

        content = ShulClusterPopupView.as_view()(
            popup_GET(
                cluster_key=large.cluster_key,
                **{"rooms__relative_size": RelativeSize.L},
            )
        ).content.decode()

        assert large.name in content
        assert small.name not in content

    def test_invalid_filter_value_returns_nothing_rather_than_everything(popup_GET, test_shul):
        """
        Mirrors django_filter's strict FilterView behavior: an invalid bound
        filter must not silently fall back to an unfiltered queryset.
        """
        content = ShulClusterPopupView.as_view()(
            popup_GET(
                cluster_key=test_shul.cluster_key,
                **{"rooms__relative_size": "NOT_A_REAL_CHOICE"},
            )
        ).content.decode()

        assert test_shul.name not in content


def describe_exclude_param():
    def test_excludes_the_given_shul(popup_GET):
        keep = Shul.objects.create(name="Keep", latitude=40.7128, longitude=-74.0060)
        drop = Shul.objects.create(name="Drop", latitude=40.7129, longitude=-74.0061)

        content = ShulClusterPopupView.as_view()(
            popup_GET(cluster_key=keep.cluster_key, exclude=str(drop.pk))
        ).content.decode()

        assert keep.name in content
        assert drop.name not in content

    def test_non_numeric_exclude_does_not_error(popup_GET, test_shul):
        response = ShulClusterPopupView.as_view()(
            popup_GET(cluster_key=test_shul.cluster_key, exclude="not-a-number")
        )

        assert response.status_code == 200
        assert test_shul.name in response.content.decode()


def test_expands_only_the_selected_shul(popup_GET):
    first = Shul.objects.create(name="First", latitude=40.7128, longitude=-74.0060)
    second = Shul.objects.create(name="Second", latitude=40.7129, longitude=-74.0061)

    soup = BeautifulSoup(
        ShulClusterPopupView.as_view()(
            popup_GET(cluster_key=first.cluster_key, selected_shul=str(first.pk))
        ).content.decode(),
        features="html.parser",
    )

    assert "show" in soup.find(id=f"shul-{first.pk}")["class"]
    assert "show" not in soup.find(id=f"shul-{second.pk}")["class"]


def test_query_count_does_not_scale_with_room_count(popup_GET, django_assert_num_queries):
    """
    Locks in the rooms prefetch (shul.rooms.all|length / {% if shul.rooms.all %}
    in shul_accordion_item.html): more rooms must not mean more queries.

    Uses an anonymous request to sidestep AbusePreventionMixin: its rate-limit cache
    (a DatabaseCache) takes a different query path on a cold vs. a warm cache key, which
    would otherwise swing the count between these two calls for reasons unrelated to rooms.
    """
    few_rooms = Shul.objects.create(name="Few Rooms", latitude=40.7128, longitude=-74.0060)
    few_rooms.rooms.create(name="r", relative_size=RelativeSize.L, see_hear_score=SeeHearScore._5)

    many_rooms = Shul.objects.create(name="Many Rooms", latitude=31.7683, longitude=35.2137)
    for i in range(5):
        many_rooms.rooms.create(
            name=f"r{i}", relative_size=RelativeSize.L, see_hear_score=SeeHearScore._5
        )

    anon = AnonymousUser()
    with CaptureQueriesContext(connection) as few_room_queries:
        ShulClusterPopupView.as_view()(popup_GET(cluster_key=few_rooms.cluster_key, user=anon))

    with django_assert_num_queries(len(few_room_queries.captured_queries)):
        ShulClusterPopupView.as_view()(popup_GET(cluster_key=many_rooms.cluster_key, user=anon))


def describe_authenticated_users():
    def test_sees_full_membership_and_real_count(popup_GET):
        first = Shul.objects.create(name="First", latitude=40.7128, longitude=-74.0060)
        second = Shul.objects.create(name="Second", latitude=40.7129, longitude=-74.0061)

        content = ShulClusterPopupView.as_view()(
            popup_GET(cluster_key=first.cluster_key)
        ).content.decode()

        assert first.name in content
        assert second.name in content
        assert "2 Shuls in this area" in content


def describe_anonymous_users():
    def test_shul_name_is_never_sent(popup_GET, test_shul):
        content = ShulClusterPopupView.as_view()(
            popup_GET(cluster_key=test_shul.cluster_key, user=AnonymousUser())
        ).content.decode()

        assert test_shul.name not in content
        assert "text-blur" in content

    def test_real_ratings_are_still_shown(popup_GET, test_shul):
        test_shul.rooms.create(name="r", relative_size=RelativeSize.L, see_hear_score=SeeHearScore._4)

        content = ShulClusterPopupView.as_view()(
            popup_GET(cluster_key=test_shul.cluster_key, user=AnonymousUser())
        ).content.decode()

        assert str(RelativeSize.L.label) in content
        assert content.count("fa-solid fa-star") == 4

    def test_only_one_shul_shown_regardless_of_cluster_size(popup_GET):
        shuls = [
            Shul.objects.create(name=f"Shul {i}", latitude=40.7128, longitude=-74.0060) for i in range(5)
        ]

        soup = BeautifulSoup(
            ShulClusterPopupView.as_view()(
                popup_GET(cluster_key=shuls[0].cluster_key, user=AnonymousUser())
            ).content.decode(),
            features="html.parser",
        )

        assert len(soup.find_all(class_="text-blur")) == 1
        page_text = soup.get_text()
        for shul in shuls:
            assert shul.name not in page_text

    def test_header_shows_generic_cta_instead_of_count(popup_GET, test_shul):
        content = ShulClusterPopupView.as_view()(
            popup_GET(cluster_key=test_shul.cluster_key, user=AnonymousUser())
        ).content.decode()

        assert "Sign in to see more" in content
        assert "Shul in this area" not in content
        assert "Shuls in this area" not in content

    def test_login_url_has_no_next_param(popup_GET, test_shul):
        """
        `next` is set client-side (wireSignInRedirect in shuls.html) since the
        popup only ever exists via JS rendering - the server-rendered link
        intentionally carries no next of its own.
        """
        content = ShulClusterPopupView.as_view()(
            popup_GET(cluster_key=test_shul.cluster_key, user=AnonymousUser())
        ).content.decode()

        link = BeautifulSoup(content, features="html.parser").find(attrs={"data-signin-link": True})
        assert link is not None
        assert "next=" not in link["href"]

    def test_empty_state_is_unaffected(popup_GET):
        response = ShulClusterPopupView.as_view()(popup_GET(cluster_key="0.0_0.0", user=AnonymousUser()))

        assert "no longer available" in response.content.decode().lower()


def describe_rate_limited_users():
    """
    The abuse state machine itself is covered by app/tests/test_abuse_prevention.py; these tests
    cover what's specific to this view - a blocked user still gets a rate-limited popup, not a 429.
    """

    def test_cooldown_shows_rate_limited_popup(popup_GET, test_shul, test_user):
        state = AbuseState.get_or_create(test_user)
        state.strikes = 2
        state.cooldown_until = timezone.now() + timedelta(minutes=45)
        state.save()

        response = ShulClusterPopupView.as_view()(popup_GET(cluster_key=test_shul.cluster_key))
        content = response.content.decode()

        assert response.status_code == 200
        assert test_shul.name not in content
        assert "text-blur" in content
        assert "Too many requests" in content
        assert "minute" in content
        assert "Sign in to see more" not in content
        # The client uses this header (not the HTML) to decide whether a swapped-in popup is safe
        # to cache - see onPopupContentSwapped's rateLimited flag in shuls.html.
        assert response["X-Abuse-Enforcement"] == "rate_limited"

    def test_permanent_ban_shows_restricted_message(popup_GET, test_shul, test_user):
        state = AbuseState.get_or_create(test_user)
        state.strikes = config.ABUSE_PERMANENT_BAN_THRESHOLD
        state.save()

        response = ShulClusterPopupView.as_view()(popup_GET(cluster_key=test_shul.cluster_key))
        content = response.content.decode()

        assert response.status_code == 200
        assert "Restricted" in content
        assert test_shul.name not in content

    def test_captcha_pending_returns_captcha_modal_not_popup(popup_GET, test_shul, test_user):
        state = AbuseState.get_or_create(test_user)
        state.strikes = config.ABUSE_CAPTCHA_THRESHOLD
        state.save()

        response = ShulClusterPopupView.as_view()(popup_GET(cluster_key=test_shul.cluster_key))

        assert response["X-Abuse-Enforcement"] == "captcha"
        assert response["HX-Retarget"] == "#abuse-modal-container"
        assert test_shul.name not in response.content.decode()

    def test_captcha_next_url_points_at_the_map_not_the_bare_fragment(popup_GET, test_shul, test_user):
        """
        The default next_url (this endpoint's own path) has no base template - it must be
        overridden here, or abuse_modal.js's JS fallback (when the popup element is gone by the
        time CAPTCHA is solved) and any non-htmx request would land on an unstyled fragment.
        """
        state = AbuseState.get_or_create(test_user)
        state.strikes = config.ABUSE_CAPTCHA_THRESHOLD
        state.save()

        response = ShulClusterPopupView.as_view()(
            popup_GET(cluster_key=test_shul.cluster_key, selected_shul=str(test_shul.pk))
        )

        modal = BeautifulSoup(response.content.decode(), features="html.parser").find(
            id="abuse-captcha-modal"
        )
        assert modal["data-next"] == f"/?selectedShul={test_shul.pk}"

    def test_rate_limited_request_does_not_consume_budget(popup_GET, test_shul, test_user):
        """
        The recovery path: hammering the popup while blocked must not add strikes or extend the
        block - AbusePreventionMixin.dispatch returns from get_blocked_response before it ever
        reaches consume_rate_budget/record_abuse_violation.
        """
        state = AbuseState.get_or_create(test_user)
        state.strikes = 2
        state.cooldown_until = timezone.now() + timedelta(minutes=45)
        state.points_in_episode = 4
        state.save()

        ShulClusterPopupView.as_view()(popup_GET(cluster_key=test_shul.cluster_key))

        state.refresh_from_db()
        assert state.points_in_episode == 4
