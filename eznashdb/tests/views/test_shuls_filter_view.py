import pytest
from bs4 import BeautifulSoup

from eznashdb.enums import RelativeSize, SeeHearScore
from eznashdb.models import Shul
from eznashdb.views import ShulsFilterView


@pytest.fixture
def GET_request(rf_GET):
    return rf_GET("eznashdb:shuls")


def test_shows_app_name(GET_request):
    response = ShulsFilterView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert "Ezrat Nashim Database" in soup.get_text()


def test_shows_room_name(GET_request, test_shul):
    room = test_shul.rooms.create(name="test_room")

    response = ShulsFilterView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert room.name in str(soup)


def describe_rooms():
    @pytest.mark.parametrize(("relative_size"), list(RelativeSize))
    def test_shows_room_relative_size(test_shul, GET_request, relative_size):
        test_shul.rooms.create(name="test_room", relative_size=relative_size)

        response = ShulsFilterView.as_view()(GET_request)
        soup = BeautifulSoup(str(response.render().content), features="html.parser")

        assert relative_size.value in str(soup)

    def test_displays_not_set_for_unknown_relative_size(test_shul, GET_request):
        test_shul.rooms.create(name="test_room", relative_size="", see_hear_score=SeeHearScore._3)

        response = ShulsFilterView.as_view()(GET_request)
        soup = BeautifulSoup(str(response.render().content), features="html.parser")

        assert "not set" in str(soup).lower()

    @pytest.mark.parametrize(("see_hear_score"), list(SeeHearScore))
    def test_shows_room_see_hear_score(test_shul, GET_request, see_hear_score):
        test_shul.rooms.create(name="test_room", see_hear_score=see_hear_score)

        response = ShulsFilterView.as_view()(GET_request)
        soup = BeautifulSoup(str(response.render().content), features="html.parser")
        marker_script = soup.find(id="shul-markers-js")

        expected_filled_star_count = int(see_hear_score.value)
        expected_empty_star_count = 5 - expected_filled_star_count

        filled_class = "fa-solid fa-star"
        empty_class = "fa-regular fa-star"

        assert str(marker_script).count(filled_class) == expected_filled_star_count
        assert str(marker_script).count(empty_class) == expected_empty_star_count

    def test_shows_not_set_for_unknown_see_hear_score(test_shul, GET_request):
        test_shul.rooms.create(name="test_room", see_hear_score="", relative_size=RelativeSize.M)

        response = ShulsFilterView.as_view()(GET_request)
        soup = BeautifulSoup(str(response.render().content), features="html.parser")

        assert "not set" in str(soup).lower()


def describe_exact_pin_behavior():
    def test_justSaved_shul_in_context_and_excluded_from_clusters(rf_GET):
        """When justSaved param is present, shul should be in exact_pin_shul and excluded from clusters"""
        shul = Shul.objects.create(name="Test Shul", latitude=40.7128, longitude=-74.0060)
        request = rf_GET("eznashdb:shuls", query_params={"justSaved": str(shul.id)})

        response = ShulsFilterView.as_view()(request)
        context = response.context_data

        # Shul should be in exact_pin_shul
        assert context["exact_pin_shul"] == shul
        # But not in any cluster (shul_clusters values are lists of shuls per cluster)
        all_clustered_shuls = [s for cluster in context["shul_clusters"].values() for s in cluster]
        assert shul not in all_clustered_shuls

    def test_cluster_offset_calculated_for_nearby_cluster(rf_GET):
        """When exact pin is close to a cluster, offset should be calculated with correct structure"""
        # Create shuls that round to same coords (40.70, -74.00) and jitter close to exact position
        exact_shul = Shul.objects.create(name="Exact Shul", latitude=40.699, longitude=-74.001)

        # Create another shul at similar coords to force same cluster
        _nearby_shul = Shul.objects.create(name="Nearby Shul", latitude=40.699, longitude=-74.001)

        request = rf_GET("eznashdb:shuls", query_params={"justSaved": str(exact_shul.id)})

        response = ShulsFilterView.as_view()(request)
        context = response.context_data

        offset = context["cluster_offset"]
        assert offset is not None
        assert "cluster_key" in offset
        assert "offset_lon" in offset
        assert isinstance(offset["cluster_key"], str)
        assert isinstance(offset["offset_lon"], (int, float))
