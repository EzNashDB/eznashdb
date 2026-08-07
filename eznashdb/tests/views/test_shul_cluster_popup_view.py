import pytest
from bs4 import BeautifulSoup
from django.db import connection
from django.test.utils import CaptureQueriesContext
from waffle.testutils import override_flag

from eznashdb.enums import KaddishPolicy, RelativeSize, SeeHearScore
from eznashdb.models import Shul
from eznashdb.views import ShulClusterPopupView


@pytest.fixture
def popup_GET(rf_GET):
    def _get(**query_params):
        return rf_GET("eznashdb:cluster_popup", query_params=query_params, htmx=True)

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


def describe_kaddish_flag():
    @override_flag("kaddish", active=True)
    def shows_kaddish_policy_when_flag_active(popup_GET, test_shul):
        test_shul.kaddish_policy = KaddishPolicy.CAN_SAY_ALONE
        test_shul.save()

        content = ShulClusterPopupView.as_view()(
            popup_GET(cluster_key=test_shul.cluster_key)
        ).content.decode()

        assert "Kaddish:" in content


@override_flag("kaddish", active=True)
def test_query_count_does_not_scale_with_room_count(popup_GET, django_assert_num_queries):
    """
    Locks in the rooms prefetch (shul.rooms.all|length / {% if shul.rooms.all %}
    in shul_accordion_item.html): more rooms must not mean more queries.
    """
    few_rooms = Shul.objects.create(name="Few Rooms", latitude=40.7128, longitude=-74.0060)
    few_rooms.rooms.create(name="r", relative_size=RelativeSize.L, see_hear_score=SeeHearScore._5)

    many_rooms = Shul.objects.create(name="Many Rooms", latitude=31.7683, longitude=35.2137)
    for i in range(5):
        many_rooms.rooms.create(
            name=f"r{i}", relative_size=RelativeSize.L, see_hear_score=SeeHearScore._5
        )

    # The waffle flag's first-ever lookup in a test process does several
    # bootstrap queries (cache population); warm it up before measuring so
    # that one-time cost doesn't pollute the comparison below.
    ShulClusterPopupView.as_view()(popup_GET(cluster_key="warmup"))

    with CaptureQueriesContext(connection) as few_room_queries:
        ShulClusterPopupView.as_view()(popup_GET(cluster_key=few_rooms.cluster_key))

    with django_assert_num_queries(len(few_room_queries.captured_queries)):
        ShulClusterPopupView.as_view()(popup_GET(cluster_key=many_rooms.cluster_key))
